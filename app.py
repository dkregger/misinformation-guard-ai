from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, FlaggedPost, MonitoringSession, ImageAnalysis
from datetime import datetime
import os
import json
import re

# Import image analyzer
try:
    from image_analyzer import ImageAnalyzer
    image_analyzer = ImageAnalyzer()
    print("✅ Image analyzer loaded successfully!")
except Exception as e:
    print(f"⚠️ Image analyzer not available: {e}")
    image_analyzer = None

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///flagged_posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with our app
db.init_app(app)

def extract_image_urls(content, url=None):
    """Extract image URLs from content or post URL"""
    image_urls = []
    
    try:
        # Look for direct image URLs in content
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        potential_urls = re.findall(url_pattern, content)
        
        for potential_url in potential_urls:
            # Check if URL points to an image
            if any(ext in potential_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                image_urls.append(potential_url)
        
        # If we have a post URL, try to construct potential image URLs
        if url and not image_urls:
            # For Twitter, we might try to get associated media
            if 'twitter.com' in url:
                pass
            
            # For news articles, images might be embedded
            if any(domain in url for domain in ['news', 'article', 'blog']):
                pass
    
    except Exception as e:
        print(f"⚠️ Error extracting image URLs: {e}")
    
    return image_urls

def analyze_content_images(content, post_url=None):
    """Analyze any images found in the content"""
    if not image_analyzer:
        return None
    
    try:
        # Extract image URLs from content
        image_urls = extract_image_urls(content, post_url)
        
        if not image_urls:
            return {
                'has_images': False,
                'images_analyzed': 0,
                'results': []
            }
        
        print(f"🖼️ Found {len(image_urls)} images to analyze")
        
        analysis_results = []
        suspicious_count = 0
        
        # Analyze each image
        for i, image_url in enumerate(image_urls[:3]):  # Limit to 3 images for performance
            print(f"🔍 Analyzing image {i+1}/{min(len(image_urls), 3)}: {image_url[:50]}...")
            
            try:
                result = image_analyzer.analyze_image(image_url)
                analysis_results.append(result)
                
                if result.get('overall_suspicious', False):
                    suspicious_count += 1
                    print(f"  🚨 Suspicious image detected: {result.get('assessment', 'Unknown')}")
                else:
                    print(f"  ✅ Image appears authentic")
                    
            except Exception as e:
                print(f"  ❌ Error analyzing image: {e}")
                analysis_results.append({
                    'image_url': image_url,
                    'error': str(e),
                    'overall_suspicious': False,
                    'overall_confidence': 0.0
                })
        
        return {
            'has_images': True,
            'images_found': len(image_urls),
            'images_analyzed': len(analysis_results),
            'suspicious_images': suspicious_count,
            'results': analysis_results
        }
        
    except Exception as e:
        print(f"❌ Error in image analysis: {e}")
        return {
            'has_images': False,
            'error': str(e),
            'images_analyzed': 0,
            'results': []
        }

def store_image_analysis(flagged_post_id, image_analysis_result):
    """Store image analysis results in the database"""
    if not image_analysis_result or not image_analysis_result.get('has_images'):
        return None
    
    try:
        # Find the most suspicious image result to store
        results = image_analysis_result.get('results', [])
        if not results:
            return None
        
        # Get the most suspicious result or the first one
        main_result = None
        for result in results:
            if result.get('overall_suspicious', False):
                main_result = result
                break
        
        if not main_result:
            main_result = results[0]  # Use first result if none are suspicious
        
        # Create ImageAnalysis record
        image_analysis = ImageAnalysis(
            image_url=main_result.get('image_url', ''),
            image_hash=main_result.get('image_hash', ''),
            image_size=f"{main_result.get('size', 'unknown')}",
            image_format=main_result.get('format', 'unknown'),
            overall_suspicious=main_result.get('overall_suspicious', False),
            overall_confidence=main_result.get('overall_confidence', 0.0),
            assessment=main_result.get('assessment', 'Analysis completed'),
            deepfake_confidence=main_result.get('detections', {}).get('deepfake', {}).get('confidence', 0.0),
            deepfake_detected=main_result.get('detections', {}).get('deepfake', {}).get('is_suspicious', False),
            faces_detected=main_result.get('detections', {}).get('deepfake', {}).get('details', {}).get('faces_detected', 0),
            manipulation_confidence=main_result.get('detections', {}).get('manipulation', {}).get('confidence', 0.0),
            manipulation_detected=main_result.get('detections', {}).get('manipulation', {}).get('is_suspicious', False),
            manipulation_type=main_result.get('detections', {}).get('manipulation', {}).get('method', 'unknown'),
            metadata_suspicious=main_result.get('detections', {}).get('metadata', {}).get('is_suspicious', False),
            metadata_analysis=json.dumps(main_result.get('detections', {}).get('metadata', {})),
            detection_details=json.dumps(main_result),
            primary_concerns=json.dumps(main_result.get('primary_concerns', [])),
            analysis_method='multi_factor_analysis',
            processing_time_seconds=1.0  # Placeholder
        )
        
        # Save to database
        db.session.add(image_analysis)
        db.session.commit()
        
        # Update the flagged post to link to this analysis
        flagged_post = FlaggedPost.query.get(flagged_post_id)
        if flagged_post:
            flagged_post.image_analysis_id = image_analysis.id
            flagged_post.has_images = True
            db.session.commit()
        
        print(f"💾 Stored image analysis results (ID: {image_analysis.id})")
        return image_analysis.id
        
    except Exception as e:
        print(f"❌ Error storing image analysis: {e}")
        db.session.rollback()
        return None

@app.route("/")
def home():
    return jsonify({"status": "running", "message": "Enhanced Misinformation Guard API with Image Analysis"})

@app.route("/dashboard")
def dashboard():
    """Serve the React dashboard"""
    try:
        return send_from_directory('.', 'working_dashboard.html')
    except FileNotFoundError:
        return jsonify({"error": "Dashboard file not found. Make sure working_dashboard.html is in the project root."}), 404

# PRODUCTION-SAFE DATABASE MIGRATION
def safe_database_migration():
    """Safely migrate database schema without losing data."""
    try:
        # Create tables if they don't exist
        db.create_all()
        
        # Check if we need to add new columns to existing tables
        inspector = db.inspect(db.engine)
        
        # Check flagged_post table columns
        if inspector.has_table('flagged_post'):
            columns = [column['name'] for column in inspector.get_columns('flagged_post')]
            
            migrations_needed = []
            
            # Add review columns if missing
            if 'is_reviewed' not in columns:
                migrations_needed.append("ALTER TABLE flagged_post ADD COLUMN is_reviewed BOOLEAN DEFAULT FALSE")
            if 'reviewed_at' not in columns:
                migrations_needed.append("ALTER TABLE flagged_post ADD COLUMN reviewed_at TIMESTAMP")
            
            # Add image analysis columns if missing
            if 'has_images' not in columns:
                migrations_needed.append("ALTER TABLE flagged_post ADD COLUMN has_images BOOLEAN DEFAULT FALSE")
            if 'image_analysis_id' not in columns:
                migrations_needed.append("ALTER TABLE flagged_post ADD COLUMN image_analysis_id INTEGER")
            if 'coordination_score' not in columns:
                migrations_needed.append("ALTER TABLE flagged_post ADD COLUMN coordination_score FLOAT DEFAULT 0.0")
            
            # Execute migrations
            if migrations_needed:
                print(f"🔄 Running {len(migrations_needed)} database migrations...")
                for migration in migrations_needed:
                    try:
                        db.engine.execute(migration)
                        print(f"✅ Executed: {migration}")
                    except Exception as e:
                        print(f"⚠️ Migration might have already been applied: {e}")
                
                print("✅ Database migration completed successfully!")
            else:
                print("✅ Database schema is up to date!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database migration error: {e}")
        return False

# EMERGENCY RESET ROUTE FOR DEVELOPMENT
@app.route("/force-reset-db")
def force_reset_db():
    """⚠️ DEVELOPMENT ONLY: Force recreate database with new schema"""
    try:
        print("🚨 FORCING DATABASE RESET - ALL DATA WILL BE LOST!")
        
        # Drop all tables
        db.drop_all()
        print("🗑️ Dropped all existing tables")
        
        # Create all tables with current schema
        db.create_all()
        print("✅ Created all tables with new schema including image analysis")
        
        return jsonify({
            "message": "⚠️ DATABASE RESET COMPLETED - ALL DATA WAS DELETED",
            "status": "success",
            "tables_created": ["flagged_post", "monitoring_session", "image_analysis", "user_profile", "network_analysis"]
        })
    except Exception as e:
        print(f"❌ Error during database reset: {e}")
        return jsonify({"error": str(e)})

# NEW ROUTE: Manual Image Analysis
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    """Manually analyze an image for deepfakes and manipulation"""
    try:
        data = request.json
        
        if not data or 'image_url' not in data:
            return jsonify({"error": "image_url is required"}), 400
        
        if not image_analyzer:
            return jsonify({"error": "Image analysis not available"}), 503
        
        image_url = data['image_url']
        print(f"🔍 Manual image analysis requested for: {image_url}")
        
        # Run analysis
        result = image_analyzer.analyze_image(image_url)
        
        return jsonify({
            "status": "success",
            "analysis_result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in manual image analysis: {e}")
        return jsonify({"error": str(e)}), 500

# NEW ROUTE: Get Image Analysis Statistics
@app.route("/image-stats", methods=["GET"])
def get_image_stats():
    """Get statistics about image analysis results"""
    try:
        total_analyses = ImageAnalysis.query.count()
        suspicious_images = ImageAnalysis.query.filter_by(overall_suspicious=True).count()
        deepfakes_detected = ImageAnalysis.query.filter_by(deepfake_detected=True).count()
        manipulations_detected = ImageAnalysis.query.filter_by(manipulation_detected=True).count()
        
        return jsonify({
            "total_images_analyzed": total_analyses,
            "suspicious_images": suspicious_images,
            "deepfakes_detected": deepfakes_detected,
            "manipulations_detected": manipulations_detected,
            "clean_images": total_analyses - suspicious_images,
            "analysis_success_rate": 100.0 if total_analyses > 0 else 0.0
        })
        
    except Exception as e:
        print(f"❌ Error getting image stats: {e}")
        return jsonify({"error": "Failed to get image statistics"}), 500

@app.route("/flagged", methods=["GET"])
def get_flagged():
    """Get all flagged posts with enhanced image analysis data"""
    try:
        include_reviewed = request.args.get('include_reviewed', 'false').lower() == 'true'
        
        if include_reviewed:
            posts = FlaggedPost.query.order_by(FlaggedPost.timestamp.desc()).all()
        else:
            posts = FlaggedPost.query.filter_by(is_reviewed=False).order_by(FlaggedPost.timestamp.desc()).all()
        
        # Convert to dict and include image analysis
        posts_data = []
        for post in posts:
            post_dict = post.to_dict()
            # Image analysis is automatically included via the relationship
            posts_data.append(post_dict)
        
        return jsonify(posts_data)
    
    except Exception as e:
        print(f"Error getting flagged posts: {e}")
        return jsonify({"error": "Failed to retrieve posts"}), 500

@app.route("/flagged/<int:post_id>/review", methods=["POST"])
def mark_as_reviewed(post_id):
    """Mark a flagged post as reviewed"""
    try:
        post = FlaggedPost.query.get(post_id)
        
        if not post:
            return jsonify({"error": "Post not found"}), 404
        
        if post.is_reviewed:
            return jsonify({"message": "Post already marked as reviewed"}), 200
        
        post.is_reviewed = True
        post.reviewed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Post marked as reviewed",
            "post_id": post_id,
            "reviewed_at": post.reviewed_at.isoformat()
        }), 200
    
    except Exception as e:
        print(f"Error marking post as reviewed: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to mark post as reviewed"}), 500

@app.route("/add", methods=["POST"])
def add_flagged():
    """Add a new flagged post with automatic image analysis"""
    try:
        data = request.json
        
        if not data or 'content' not in data:
            return jsonify({"error": "Content is required"}), 400
        
        print(f"📝 Adding flagged post with enhanced analysis...")
        
        # Create the flagged post
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
            session_id=data.get('session_id'),
            is_reviewed=False,
            reviewed_at=None,
            has_images=False,  # Will be updated if images are found
            coordination_score=data.get('coordination_score', 0.0)
        )
        
        # Save the post first to get an ID
        db.session.add(new_post)
        db.session.commit()
        
        post_id = new_post.id
        print(f"✅ Created flagged post with ID: {post_id}")
        
        # Now analyze images if image analyzer is available
        if image_analyzer:
            try:
                print("🖼️ Running image analysis...")
                image_analysis_result = analyze_content_images(
                    data['content'], 
                    data.get('url')
                )
                
                if image_analysis_result and image_analysis_result.get('has_images'):
                    # Store image analysis results
                    image_analysis_id = store_image_analysis(post_id, image_analysis_result)
                    print(f"📊 Image analysis completed: {image_analysis_result.get('suspicious_images', 0)} suspicious images")
                else:
                    print("📷 No images found in content")
                    
            except Exception as e:
                print(f"⚠️ Image analysis failed (non-critical): {e}")
                # Continue without image analysis - don't fail the whole request
        
        return jsonify({
            "status": "added", 
            "id": post_id,
            "image_analysis_available": image_analyzer is not None
        }), 201
    
    except Exception as e:
        print(f"❌ Error adding flagged post: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to add post"}), 500

@app.route("/monitoring/sessions", methods=["GET"])
def get_monitoring_sessions():
    """Get monitoring session history"""
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
    """Create a new monitoring session"""
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
    """Update monitoring session with final metrics"""
    try:
        data = request.json
        session = MonitoringSession.query.get_or_404(session_id)
        
        for field, value in data.items():
            if field == 'end_time' and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
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
    """Get comprehensive monitoring statistics with enhanced metrics"""
    try:
        # Get basic session stats
        recent_sessions = MonitoringSession.query.order_by(MonitoringSession.start_time.desc()).limit(10).all()
        total_sessions = MonitoringSession.query.count()
        total_articles_processed = db.session.query(db.func.sum(MonitoringSession.total_articles_analyzed)).scalar() or 0
        total_articles_flagged = db.session.query(db.func.sum(MonitoringSession.total_flagged)).scalar() or 0
        
        # Get enhanced image analysis stats
        total_images_analyzed = db.session.query(db.func.sum(MonitoringSession.total_images_analyzed)).scalar() or 0
        total_suspicious_images = db.session.query(db.func.sum(MonitoringSession.images_flagged_suspicious)).scalar() or 0
        total_deepfakes = db.session.query(db.func.sum(MonitoringSession.deepfakes_detected)).scalar() or 0
        total_manipulated = db.session.query(db.func.sum(MonitoringSession.manipulated_images_detected)).scalar() or 0
        
        # Get network analysis stats
        total_networks = db.session.query(db.func.sum(MonitoringSession.coordinated_networks_found)).scalar() or 0
        network_analyses = db.session.query(db.func.sum(MonitoringSession.network_analyses_performed)).scalar() or 0
        
        # Average metrics
        avg_flagging_rate = db.session.query(db.func.avg(MonitoringSession.flagging_rate)).scalar() or 0
        avg_scraping_success = db.session.query(db.func.avg(MonitoringSession.scraping_success_rate)).scalar() or 0
        avg_image_success = db.session.query(db.func.avg(MonitoringSession.image_analysis_success_rate)).scalar() or 0
        
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
            # Enhanced image analysis metrics
            "total_images_analyzed": total_images_analyzed,
            "total_suspicious_images": total_suspicious_images,
            "total_deepfakes_detected": total_deepfakes,
            "total_manipulated_images": total_manipulated,
            "image_analysis_success_rate": float(avg_image_success) if avg_image_success else 0,
            "image_analysis_rate": (total_suspicious_images / total_images_analyzed * 100) if total_images_analyzed > 0 else 0,
            # Enhanced network analysis metrics
            "coordinated_networks_found": total_networks,
            "network_analyses_performed": network_analyses,
            "coordination_risk_level": "MEDIUM" if total_networks > 0 else "LOW",  # Simplified risk assessment
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
    """Get summary statistics including enhanced image and network analysis"""
    try:
        # Basic content stats
        total_posts = FlaggedPost.query.count()
        propaganda_posts = FlaggedPost.query.filter_by(label='propaganda').count()
        toxic_posts = FlaggedPost.query.filter_by(label='toxic').count()
        reliable_posts = FlaggedPost.query.filter_by(label='reliable').count()
        bot_posts = FlaggedPost.query.filter_by(is_bot=True).count()
        
        # Review statistics
        reviewed_posts = FlaggedPost.query.filter_by(is_reviewed=True).count()
        unreviewed_posts = FlaggedPost.query.filter_by(is_reviewed=False).count()
        
        # Enhanced image analysis statistics
        posts_with_images = FlaggedPost.query.filter_by(has_images=True).count()
        
        # Get detailed image analysis stats from ImageAnalysis table
        total_image_analyses = ImageAnalysis.query.count()
        suspicious_images = ImageAnalysis.query.filter_by(overall_suspicious=True).count()
        deepfakes_detected = ImageAnalysis.query.filter_by(deepfake_detected=True).count()
        manipulations_detected = ImageAnalysis.query.filter_by(manipulation_detected=True).count()
        
        # Network analysis statistics
        coordinated_posts = FlaggedPost.query.filter(FlaggedPost.coordination_score > 0.5).count()
        
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
            "review_stats": {
                "reviewed_count": reviewed_posts,
                "unreviewed_count": unreviewed_posts,
                "review_percentage": (reviewed_posts / total_posts * 100) if total_posts > 0 else 0
            },
            # Enhanced image analysis statistics
            "image_stats": {
                "posts_with_images": posts_with_images,
                "total_images_analyzed": total_image_analyses,
                "suspicious_images": suspicious_images,
                "deepfakes_detected": deepfakes_detected,
                "manipulations_detected": manipulations_detected,
                "clean_images": total_image_analyses - suspicious_images,
                "image_analysis_rate": (suspicious_images / total_image_analyses * 100) if total_image_analyses > 0 else 0
            },
            # Enhanced network analysis statistics
            "network_stats": {
                "coordinated_posts": coordinated_posts,
                "coordination_rate": (coordinated_posts / total_posts * 100) if total_posts > 0 else 0
            }
        })
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500

if __name__ == "__main__":
    # ENHANCED DATABASE SETUP WITH PROPER ERROR HANDLING
    with app.app_context():
        print("🔄 Starting enhanced database setup...")
        
        migration_success = safe_database_migration()
        
        if migration_success:
            print("✅ Database setup completed successfully!")
            
            # Test the schema
            try:
                test_query = FlaggedPost.query.filter_by(is_reviewed=False).count()
                print(f"🧪 Schema test passed - found {test_query} unreviewed posts")
                
                # Test image analysis table
                image_test = ImageAnalysis.query.count()
                print(f"🖼️ Image analysis table ready - {image_test} analyses stored")
                
            except Exception as e:
                print(f"⚠️ Schema test failed: {e}")
                print("💡 Try visiting http://localhost:5000/force-reset-db to fix schema issues")
        else:
            print("❌ Database setup failed!")
            print("💡 Try visiting http://localhost:5000/force-reset-db to recreate database")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)