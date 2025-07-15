from flask import Flask, request, jsonify
from models import db, FlaggedPost
import os

app = Flask(__name__)

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
    return "Misinformation Guard API is running."

@app.route("/flagged", methods=["GET"])
def get_flagged():
    """
    Get all flagged posts from the database.
    Returns them as JSON for our React app to consume.
    """
    try:
        # Query all flagged posts, ordered by most recent first
        posts = FlaggedPost.query.order_by(FlaggedPost.timestamp.desc()).all()
        
        # Convert each post to a dictionary
        posts_data = [post.to_dict() for post in posts]
        
        return jsonify(posts_data)
    
    except Exception as e:
        print(f"Error getting flagged posts: {e}")
        return jsonify({"error": "Failed to retrieve posts"}), 500

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
            source=data.get('source', 'unknown')
        )
        
        # Add to database
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({"status": "added", "id": new_post.id}), 201
    
    except Exception as e:
        print(f"Error adding flagged post: {e}")
        db.session.rollback()  # Undo any partial changes
        return jsonify({"error": "Failed to add post"}), 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """
    Get summary statistics for the dashboard.
    """
    try:
        total_posts = FlaggedPost.query.count()
        propaganda_posts = FlaggedPost.query.filter_by(label='propaganda').count()
        toxic_posts = FlaggedPost.query.filter_by(label='toxic').count()
        reliable_posts = FlaggedPost.query.filter_by(label='reliable').count()
        
        return jsonify({
            "total_flagged": total_posts,
            "propaganda_count": propaganda_posts,
            "toxic_count": toxic_posts,
            "reliable_count": reliable_posts,
            "flagged_content": propaganda_posts + toxic_posts
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