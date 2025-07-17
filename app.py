from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, FlaggedPost, MonitoringSession
from datetime import datetime
import os

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Database configuration
# On Heroku, DATABASE_URL is automatically set
# For local development, we'll use SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Heroku uses 'postgres://' but SQLAlchemy needs 'postgresql://'
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///flagged_posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with our app
db.init_app(app)

@app.route("/")
def home():
    return jsonify({"status": "running", "message": "Misinformation Guard API is running."})

@app.route("/dashboard")
def dashboard():
    """Serve the React dashboard"""
    try:
        return send_from_directory('.', 'working_dashboard.html')
    except FileNotFoundError:
        return jsonify({"error": "Dashboard file not found. Make sure working_dashboard.html is in the project root."}), 404

@app.route("/flagged", methods=["GET"])
def get_flagged():
    """
    Get all flagged posts from the database.
    By default, only returns unreviewed posts for the dashboard.
    Add ?include_reviewed=true to see all posts.
    """
    try:
        # Check if we should include reviewed posts
        include_reviewed = request.args.get('include_reviewed', 'false').lower() == 'true'
        
        # Build query based on review status
        if include_reviewed:
            # Get all posts (reviewed and unreviewed)
            posts = FlaggedPost.query.order_by(FlaggedPost.timestamp.desc()).all()
        else:
            # Only get unreviewed posts (default behavior for dashboard)
            posts = FlaggedPost.query.filter_by(is_reviewed=False).order_by(FlaggedPost.timestamp.desc()).all()
        
        # Convert each post to a dictionary
        posts_data = [post.to_dict() for post in posts]
        
        return jsonify(posts_data)
    
    except Exception as e:
        print(f"Error getting flagged posts: {e}")
        return jsonify({"error": "Failed to retrieve posts"}), 500

# NEW ROUTE: Mark content as reviewed
@app.route("/flagged/<int:post_id>/review", methods=["POST"])
def mark_as_reviewed(post_id):
    """
    Mark a flagged post as reviewed.
    This removes it from the dashboard display but keeps it in the database.
    
    Args:
        post_id: The ID of the flagged post to mark as reviewed
    """
    try:
        # Find the post in the database
        post = FlaggedPost.query.get(post_id)
        
        if not post:
            return jsonify({"error": "Post not found"}), 404
        
        if post.is_reviewed:
            return jsonify({"message": "Post already marked as reviewed"}), 200
        
        # Mark as reviewed and set timestamp
        post.is_reviewed = True
        post.reviewed_at = datetime.utcnow()
        
        # Save changes to database
        db.session.commit()
        
        return jsonify({
            "message": "Post marked as reviewed",
            "post_id": post_id,
            "reviewed_at": post.reviewed_at.isoformat()
        }), 200
    
    except Exception as e:
        print(f"Error marking post as reviewed: {e}")
        db.session.rollback()  # Undo any partial changes
        return jsonify({"error": "Failed to mark post as reviewed"}), 500

# NEW ROUTE: Get review statistics
@app.route("/review-stats", methods=["GET"])
def get_review_stats():
    """
    Get statistics about reviewed vs unreviewed content.
    Useful for dashboard metrics.
    """
    try:
        total_flagged = FlaggedPost.query.count()
        reviewed_count = FlaggedPost.query.filter_by(is_reviewed=True).count()
        unreviewed_count = FlaggedPost.query.filter_by(is_reviewed=False).count()
        
        return jsonify({
            "total_flagged": total_flagged,
            "reviewed_count": reviewed_count,
            "unreviewed_count": unreviewed_count,
            "review_percentage": (reviewed_count / total_flagged * 100) if total_flagged > 0 else 0
        })
    
    except Exception as e:
        print(f"Error getting review stats: {e}")
        return jsonify({"error": "Failed to get review statistics"}), 500

@app.route("/add", methods=["POST"])
def add_flagged():
    """
    Add a new flagged post to the database.
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'content' not in data:
            return jsonify({"error": "Content is required"}), 400
        
        # Create a new FlaggedPost object
        new_post = FlaggedPost(
            content=data['content'],
            confidence=data.get('confidence', 0.0),
            label=data.get('label', 'unknown'),
            url=data.get('url'),
            source=data.get('source', 'unknown'),
            username=data.get('username'),
            is_bot=data.get('is_bot', False),
            bot_confidence=data.get('bot_confidence', 0.0),
            bot_reasons=data.get('bot_reasons'),
            session_id=data.get('session_id'),  # Link to monitoring session
            # Review fields default to False/None as defined in model
        )
        
        # Add to database
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({"status": "added", "id": new_post.id}), 201
    
    except Exception as e:
        print(f"Error adding flagged post: {e}")
        db.session.rollback()  # Undo any partial changes
        return jsonify({"error": "Failed to add post"}), 500

@app.route("/monitoring/sessions", methods=["GET"])
def get_monitoring_sessions():
    """
    Get monitoring session history with performance metrics
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        sessions = MonitoringSession.query.order_by(MonitoringSession.start_time.desc()).limit(limit).all()
        
        sessions_data = [session.to_dict() for session in sessions]
        return jsonify(sessions_data)
    
    except Exception as e:
        print(f"Error getting monitoring sessions: {e}")
        return jsonify({"error": "Failed to retrieve monitoring sessions"}), 500

@app.route("/monitoring/sessions", methods=["POST"])
def create_monitoring_session():
    """
    Create a new monitoring session
    """
    try:
        data = request.json
        
        new_session = MonitoringSession(
            session_type=data.get('session_type', 'unknown'),
            use_real_data=data.get('use_real_data', False)
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        return jsonify({"session_id": new_session.id, "status": "created"}), 201
    
    except Exception as e:
        print(f"Error creating monitoring session: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create monitoring session"}), 500

@app.route("/monitoring/sessions/<int:session_id>", methods=["PUT"])
def update_monitoring_session(session_id):
    """
    Update monitoring session with final metrics
    """
    try:
        data = request.json
        session = MonitoringSession.query.get_or_404(session_id)
        
        # Update all provided fields with proper datetime conversion
        for field, value in data.items():
            if field == 'end_time' and isinstance(value, str):
                # Convert ISO string to datetime object
                try:
                    from datetime import datetime
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    # If parsing fails, use current time
                    value = datetime.utcnow()
            
            if hasattr(session, field):
                setattr(session, field, value)
        
        db.session.commit()
        
        return jsonify({"status": "updated"}), 200
    
    except Exception as e:
        print(f"Error updating monitoring session: {e}")
        db.session.rollback()
        return jsonify({"error": f"Failed to update monitoring session: {str(e)}"}), 500

@app.route("/monitoring/stats/summary", methods=["GET"])
def get_monitoring_summary():
    """
    Get comprehensive monitoring statistics
    """
    try:
        # Recent session stats (last 10 sessions)
        recent_sessions = MonitoringSession.query.order_by(MonitoringSession.start_time.desc()).limit(10).all()
        
        # Overall stats
        total_sessions = MonitoringSession.query.count()
        total_articles_processed = db.session.query(db.func.sum(MonitoringSession.total_articles_analyzed)).scalar() or 0
        total_articles_flagged = db.session.query(db.func.sum(MonitoringSession.total_flagged)).scalar() or 0
        
        # Average metrics
        avg_flagging_rate = db.session.query(db.func.avg(MonitoringSession.flagging_rate)).scalar() or 0
        avg_scraping_success = db.session.query(db.func.avg(MonitoringSession.scraping_success_rate)).scalar() or 0
        
        # Content breakdown
        total_propaganda = db.session.query(db.func.sum(MonitoringSession.propaganda_count)).scalar() or 0
        total_toxic = db.session.query(db.func.sum(MonitoringSession.toxic_count)).scalar() or 0
        total_bots = db.session.query(db.func.sum(MonitoringSession.bot_count)).scalar() or 0
        
        summary = {
            "total_sessions": total_sessions,
            "total_articles_processed": total_articles_processed,
            "total_articles_flagged": total_articles_flagged,
            "overall_flagging_rate": (total_articles_flagged / total_articles_processed * 100) if total_articles_processed > 0 else 0,
            "average_flagging_rate": float(avg_flagging_rate) if avg_flagging_rate else 0,
            "average_scraping_success_rate": float(avg_scraping_success) if avg_scraping_success else 0,
            "content_breakdown": {
                "propaganda": total_propaganda,
                "toxic": total_toxic,
                "bots": total_bots,
                "total_problematic": total_propaganda + total_toxic + total_bots
            },
            "recent_sessions": [session.to_dict() for session in recent_sessions[:5]]
        }
        
        return jsonify(summary)
    
    except Exception as e:
        print(f"Error getting monitoring summary: {e}")
        return jsonify({"error": "Failed to get monitoring summary"}), 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """
    Get summary statistics for the dashboard.
    Now includes review statistics.
    """
    try:
        total_posts = FlaggedPost.query.count()
        propaganda_posts = FlaggedPost.query.filter_by(label='propaganda').count()
        toxic_posts = FlaggedPost.query.filter_by(label='toxic').count()
        reliable_posts = FlaggedPost.query.filter_by(label='reliable').count()
        bot_posts = FlaggedPost.query.filter_by(is_bot=True).count()
        
        # NEW: Add review statistics
        reviewed_posts = FlaggedPost.query.filter_by(is_reviewed=True).count()
        unreviewed_posts = FlaggedPost.query.filter_by(is_reviewed=False).count()
        
        return jsonify({
            "total_flagged": total_posts,
            "propaganda_count": propaganda_posts,
            "toxic_count": toxic_posts,
            "reliable_count": reliable_posts,
            "bot_count": bot_posts,
            "flagged_content": propaganda_posts + toxic_posts,
            "human_vs_bot": {
                "bot_posts": bot_posts,
                "human_posts": total_posts - bot_posts
            },
            # NEW: Review statistics
            "review_stats": {
                "reviewed_count": reviewed_posts,
                "unreviewed_count": unreviewed_posts,
                "review_percentage": (reviewed_posts / total_posts * 100) if total_posts > 0 else 0
            }
        })
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500

if __name__ == "__main__":
    # Create database tables when app starts
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)