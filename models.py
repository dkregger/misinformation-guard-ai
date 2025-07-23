"""
Enhanced database models for the misinformation detection system.

This file defines the database schema for storing:
1. Original flagged content and monitoring sessions
2. Image analysis results (deepfakes, manipulation detection)
3. Network analysis results (coordinated behavior detection)
4. User network data and relationships
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Create the database object - this will be initialized by the Flask app
db = SQLAlchemy()

class FlaggedPost(db.Model):
    """
    Model for storing flagged social media posts and news articles.
    Enhanced with image and network analysis capabilities.
    """
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Content information
    content = db.Column(db.Text, nullable=False, comment="The actual text content")
    url = db.Column(db.String(255), comment="URL where content was found")
    source = db.Column(db.String(50), comment="Platform: twitter, news, etc.")
    username = db.Column(db.String(100), comment="Author username or news source")
    
    # Classification results
    confidence = db.Column(db.Float, nullable=False, comment="AI confidence score 0.0-1.0")
    label = db.Column(db.String(50), nullable=False, comment="Classification: propaganda, toxic, reliable")
    
    # Bot detection results
    is_bot = db.Column(db.Boolean, default=False, comment="True if user appears to be a bot")
    bot_confidence = db.Column(db.Float, default=0.0, comment="Bot detection confidence 0.0-1.0")
    bot_reasons = db.Column(db.Text, comment="JSON list of bot indicators")
    
    # NEW: Image analysis fields
    has_images = db.Column(db.Boolean, default=False, comment="True if post contains images")
    image_analysis_id = db.Column(db.Integer, db.ForeignKey('image_analysis.id'), comment="Link to image analysis results")
    
    # NEW: Network analysis fields
    network_analysis_id = db.Column(db.Integer, db.ForeignKey('network_analysis.id'), comment="Link to network analysis results")
    coordination_score = db.Column(db.Float, default=0.0, comment="How coordinated this post appears to be")
    
    # Review fields
    is_reviewed = db.Column(db.Boolean, default=False, comment="True if content has been human-reviewed")
    reviewed_at = db.Column(db.DateTime, nullable=True, comment="When content was marked as reviewed")
    
    # Monitoring session link
    session_id = db.Column(db.Integer, db.ForeignKey('monitoring_session.id'))
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    image_analysis = db.relationship('ImageAnalysis', backref='flagged_post', uselist=False)
    network_analysis = db.relationship('NetworkAnalysis', backref='flagged_posts')
    
    def to_dict(self):
        """Convert database record to dictionary for JSON API responses."""
        result = {
            'id': self.id,
            'content': self.content,
            'confidence': self.confidence,
            'label': self.label,
            'url': self.url,
            'source': self.source,
            'username': self.username,
            'is_bot': self.is_bot,
            'bot_confidence': self.bot_confidence,
            'bot_reasons': self.bot_reasons,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_reviewed': self.is_reviewed,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            # NEW: Enhanced analysis fields
            'has_images': self.has_images,
            'coordination_score': self.coordination_score
        }
        
        # Include image analysis if available
        if self.image_analysis:
            result['image_analysis'] = self.image_analysis.to_dict()
        
        return result
    
    def __repr__(self):
        """String representation for debugging."""
        indicators = []
        if self.is_bot:
            indicators.append("BOT")
        if self.is_reviewed:
            indicators.append("REVIEWED")
        if self.has_images:
            indicators.append("IMAGES")
        if self.coordination_score > 0.5:
            indicators.append("COORDINATED")
        
        indicator_str = f" [{', '.join(indicators)}]" if indicators else ""
        return f'<FlaggedPost {self.id}: {self.label}{indicator_str}>'


class ImageAnalysis(db.Model):
    """
    Model for storing image analysis results (deepfake and manipulation detection).
    
    Each record represents the analysis of images associated with a flagged post.
    """
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Image information
    image_url = db.Column(db.String(500), nullable=False, comment="URL of the analyzed image")
    image_hash = db.Column(db.String(64), comment="MD5 hash of the image for deduplication")
    image_size = db.Column(db.String(20), comment="Image dimensions (width x height)")
    image_format = db.Column(db.String(10), comment="Image format (JPEG, PNG, etc.)")
    
    # Analysis results
    overall_suspicious = db.Column(db.Boolean, default=False, comment="Overall assessment: is image suspicious?")
    overall_confidence = db.Column(db.Float, default=0.0, comment="Overall confidence score 0.0-1.0")
    assessment = db.Column(db.String(200), comment="Human-readable assessment")
    
    # Deepfake detection results
    deepfake_confidence = db.Column(db.Float, default=0.0, comment="Deepfake detection confidence")
    deepfake_detected = db.Column(db.Boolean, default=False, comment="True if deepfake characteristics found")
    faces_detected = db.Column(db.Integer, default=0, comment="Number of faces found in image")
    
    # Manipulation detection results
    manipulation_confidence = db.Column(db.Float, default=0.0, comment="Image manipulation confidence")
    manipulation_detected = db.Column(db.Boolean, default=False, comment="True if manipulation detected")
    manipulation_type = db.Column(db.String(100), comment="Type of manipulation detected")
    
    # Metadata analysis results
    metadata_suspicious = db.Column(db.Boolean, default=False, comment="True if metadata appears suspicious")
    metadata_analysis = db.Column(db.Text, comment="JSON details of metadata analysis")
    
    # Detection details (stored as JSON)
    detection_details = db.Column(db.Text, comment="JSON with detailed analysis results")
    primary_concerns = db.Column(db.Text, comment="JSON list of main concerns found")
    
    # Analysis metadata
    analysis_timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment="When analysis was performed")
    analysis_method = db.Column(db.String(50), comment="Analysis method used")
    processing_time_seconds = db.Column(db.Float, comment="Time taken to analyze image")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'image_url': self.image_url,
            'image_hash': self.image_hash,
            'image_size': self.image_size,
            'image_format': self.image_format,
            'overall_suspicious': self.overall_suspicious,
            'overall_confidence': self.overall_confidence,
            'assessment': self.assessment,
            'deepfake_confidence': self.deepfake_confidence,
            'deepfake_detected': self.deepfake_detected,
            'faces_detected': self.faces_detected,
            'manipulation_confidence': self.manipulation_confidence,
            'manipulation_detected': self.manipulation_detected,
            'manipulation_type': self.manipulation_type,
            'metadata_suspicious': self.metadata_suspicious,
            'metadata_analysis': json.loads(self.metadata_analysis) if self.metadata_analysis else {},
            'detection_details': json.loads(self.detection_details) if self.detection_details else {},
            'primary_concerns': json.loads(self.primary_concerns) if self.primary_concerns else [],
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'analysis_method': self.analysis_method,
            'processing_time_seconds': self.processing_time_seconds
        }
    
    def __repr__(self):
        """String representation for debugging."""
        status = "SUSPICIOUS" if self.overall_suspicious else "CLEAN"
        types = []
        if self.deepfake_detected:
            types.append("DEEPFAKE")
        if self.manipulation_detected:
            types.append("MANIPULATED")
        if self.metadata_suspicious:
            types.append("META-SUSPICIOUS")
        
        type_str = f" [{', '.join(types)}]" if types else ""
        return f'<ImageAnalysis {self.id}: {status}{type_str}>'


class NetworkAnalysis(db.Model):
    """
    Model for storing network analysis results (coordinated behavior detection).
    
    Each record represents analysis of a group of users/posts for coordination.
    """
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Analysis scope
    analysis_name = db.Column(db.String(100), comment="Name/description of this analysis")
    total_users_analyzed = db.Column(db.Integer, default=0, comment="Number of users included in analysis")
    total_posts_analyzed = db.Column(db.Integer, default=0, comment="Number of posts analyzed")
    time_window_start = db.Column(db.DateTime, comment="Start of time window analyzed")
    time_window_end = db.Column(db.DateTime, comment="End of time window analyzed")
    
    # Overall coordination assessment
    coordination_score = db.Column(db.Float, default=0.0, comment="Overall coordination score 0.0-1.0")
    risk_level = db.Column(db.String(20), comment="Risk level: MINIMAL, LOW, MEDIUM, HIGH")
    assessment = db.Column(db.String(500), comment="Human-readable assessment")
    confidence = db.Column(db.Float, default=0.0, comment="Confidence in the assessment")
    
    # Content similarity results
    similar_content_groups = db.Column(db.Integer, default=0, comment="Number of similar content groups found")
    content_similarity_score = db.Column(db.Float, default=0.0, comment="Content similarity analysis score")
    
    # Temporal pattern results
    temporal_clusters_found = db.Column(db.Integer, default=0, comment="Number of suspicious time clusters")
    regular_posting_accounts = db.Column(db.Integer, default=0, comment="Accounts with automated posting patterns")
    temporal_score = db.Column(db.Float, default=0.0, comment="Temporal pattern analysis score")
    
    # Behavior analysis results
    suspicious_users_count = db.Column(db.Integer, default=0, comment="Number of users flagged as suspicious")
    bot_like_accounts = db.Column(db.Integer, default=0, comment="Accounts showing bot-like behavior")
    behavior_score = db.Column(db.Float, default=0.0, comment="User behavior analysis score")
    
    # Network structure results
    network_clusters_found = db.Column(db.Integer, default=0, comment="Number of suspicious network clusters")
    network_density = db.Column(db.Float, default=0.0, comment="Overall network density")
    network_score = db.Column(db.Float, default=0.0, comment="Network structure analysis score")
    
    # Detailed results (stored as JSON)
    evidence_summary = db.Column(db.Text, comment="JSON list of evidence found")
    detailed_results = db.Column(db.Text, comment="JSON with complete analysis results")
    user_list = db.Column(db.Text, comment="JSON list of users included in analysis")
    suspicious_groups = db.Column(db.Text, comment="JSON details of suspicious groups found")
    
    # Analysis metadata
    analysis_timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment="When analysis was performed")
    analysis_method = db.Column(db.String(100), comment="Analysis methods used")
    processing_time_seconds = db.Column(db.Float, comment="Time taken for analysis")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'analysis_name': self.analysis_name,
            'total_users_analyzed': self.total_users_analyzed,
            'total_posts_analyzed': self.total_posts_analyzed,
            'time_window_start': self.time_window_start.isoformat() if self.time_window_start else None,
            'time_window_end': self.time_window_end.isoformat() if self.time_window_end else None,
            'coordination_score': self.coordination_score,
            'risk_level': self.risk_level,
            'assessment': self.assessment,
            'confidence': self.confidence,
            'similar_content_groups': self.similar_content_groups,
            'content_similarity_score': self.content_similarity_score,
            'temporal_clusters_found': self.temporal_clusters_found,
            'regular_posting_accounts': self.regular_posting_accounts,
            'temporal_score': self.temporal_score,
            'suspicious_users_count': self.suspicious_users_count,
            'bot_like_accounts': self.bot_like_accounts,
            'behavior_score': self.behavior_score,
            'network_clusters_found': self.network_clusters_found,
            'network_density': self.network_density,
            'network_score': self.network_score,
            'evidence_summary': json.loads(self.evidence_summary) if self.evidence_summary else [],
            'detailed_results': json.loads(self.detailed_results) if self.detailed_results else {},
            'user_list': json.loads(self.user_list) if self.user_list else [],
            'suspicious_groups': json.loads(self.suspicious_groups) if self.suspicious_groups else [],
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'analysis_method': self.analysis_method,
            'processing_time_seconds': self.processing_time_seconds
        }
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<NetworkAnalysis {self.id}: {self.risk_level} risk, {self.coordination_score:.2f} coordination>'


class UserProfile(db.Model):
    """
    Model for storing user profile data for network analysis.
    
    This stores information about users across different platforms
    for behavioral and network analysis.
    """
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User identification
    user_id = db.Column(db.String(100), nullable=False, comment="Platform-specific user ID")
    username = db.Column(db.String(100), comment="Display username")
    platform = db.Column(db.String(20), comment="Platform: twitter, facebook, etc.")
    
    # Profile information
    display_name = db.Column(db.String(200), comment="User's display name")
    bio = db.Column(db.Text, comment="User biography/description")
    follower_count = db.Column(db.Integer, default=0, comment="Number of followers")
    following_count = db.Column(db.Integer, default=0, comment="Number of accounts followed")
    post_count = db.Column(db.Integer, default=0, comment="Total number of posts")
    account_age_days = db.Column(db.Integer, comment="Age of account in days")
    verified = db.Column(db.Boolean, default=False, comment="Whether account is verified")
    
    # Analysis results
    bot_likelihood = db.Column(db.Float, default=0.0, comment="Bot detection score 0.0-1.0")
    behavior_score = db.Column(db.Float, default=0.0, comment="Behavioral analysis score")
    network_centrality = db.Column(db.Float, default=0.0, comment="User's centrality in network")
    
    # Behavioral patterns (stored as JSON)
    posting_patterns = db.Column(db.Text, comment="JSON with posting time patterns")
    interaction_patterns = db.Column(db.Text, comment="JSON with interaction patterns")
    content_patterns = db.Column(db.Text, comment="JSON with content analysis patterns")
    
    # Metadata
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, comment="When user was first analyzed")
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, comment="Last profile update")
    
    # Create composite index for efficient lookups
    __table_args__ = (
        db.Index('idx_user_platform', 'user_id', 'platform'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'platform': self.platform,
            'display_name': self.display_name,
            'bio': self.bio,
            'follower_count': self.follower_count,
            'following_count': self.following_count,
            'post_count': self.post_count,
            'account_age_days': self.account_age_days,
            'verified': self.verified,
            'bot_likelihood': self.bot_likelihood,
            'behavior_score': self.behavior_score,
            'network_centrality': self.network_centrality,
            'posting_patterns': json.loads(self.posting_patterns) if self.posting_patterns else {},
            'interaction_patterns': json.loads(self.interaction_patterns) if self.interaction_patterns else {},
            'content_patterns': json.loads(self.content_patterns) if self.content_patterns else {},
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def __repr__(self):
        """String representation for debugging."""
        bot_indicator = f" [BOT:{self.bot_likelihood:.2f}]" if self.bot_likelihood > 0.5 else ""
        return f'<UserProfile {self.user_id}@{self.platform}{bot_indicator}>'


class MonitoringSession(db.Model):
    """
    Enhanced monitoring session model with support for image and network analysis.
    """
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Session metadata
    session_type = db.Column(db.String(20), nullable=False, comment="Type: twitter, news, or both")
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Float)
    use_real_data = db.Column(db.Boolean, default=False)
    
    # Content processing metrics
    total_articles_attempted = db.Column(db.Integer, default=0)
    total_articles_successfully_scraped = db.Column(db.Integer, default=0)
    total_articles_analyzed = db.Column(db.Integer, default=0)
    total_flagged = db.Column(db.Integer, default=0)
    
    # NEW: Enhanced analysis metrics
    total_images_analyzed = db.Column(db.Integer, default=0, comment="Number of images analyzed")
    images_flagged_suspicious = db.Column(db.Integer, default=0, comment="Images flagged as suspicious")
    deepfakes_detected = db.Column(db.Integer, default=0, comment="Number of potential deepfakes found")
    manipulated_images_detected = db.Column(db.Integer, default=0, comment="Number of manipulated images found")
    
    network_analyses_performed = db.Column(db.Integer, default=0, comment="Number of network analyses run")
    coordinated_networks_found = db.Column(db.Integer, default=0, comment="Number of coordinated networks detected")
    
    # Performance rates
    scraping_success_rate = db.Column(db.Float, default=0.0)
    flagging_rate = db.Column(db.Float, default=0.0)
    image_analysis_success_rate = db.Column(db.Float, default=0.0, comment="Percentage of images successfully analyzed")
    
    # Source performance (stored as JSON strings)
    sources_attempted = db.Column(db.Text)
    sources_successful = db.Column(db.Text)
    
    # Content classification breakdown
    propaganda_count = db.Column(db.Integer, default=0)
    toxic_count = db.Column(db.Integer, default=0)
    bot_count = db.Column(db.Integer, default=0)
    reliable_count = db.Column(db.Integer, default=0)
    
    # Flag reason breakdown (JSON string)
    flag_reasons = db.Column(db.Text)
    
    # Error tracking
    error_count = db.Column(db.Integer, default=0)
    error_details = db.Column(db.Text)
    
    # Relationships
    flagged_posts = db.relationship('FlaggedPost', backref='session', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'session_type': self.session_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'total_articles_attempted': self.total_articles_attempted,
            'total_articles_successfully_scraped': self.total_articles_successfully_scraped,
            'total_articles_analyzed': self.total_articles_analyzed,
            'total_flagged': self.total_flagged,
            # NEW: Enhanced metrics
            'total_images_analyzed': self.total_images_analyzed,
            'images_flagged_suspicious': self.images_flagged_suspicious,
            'deepfakes_detected': self.deepfakes_detected,
            'manipulated_images_detected': self.manipulated_images_detected,
            'network_analyses_performed': self.network_analyses_performed,
            'coordinated_networks_found': self.coordinated_networks_found,
            # Performance rates
            'scraping_success_rate': self.scraping_success_rate,
            'flagging_rate': self.flagging_rate,
            'image_analysis_success_rate': self.image_analysis_success_rate,
            # Other fields
            'sources_attempted': json.loads(self.sources_attempted) if self.sources_attempted else {},
            'sources_successful': json.loads(self.sources_successful) if self.sources_successful else {},
            'propaganda_count': self.propaganda_count,
            'toxic_count': self.toxic_count,
            'bot_count': self.bot_count,
            'reliable_count': self.reliable_count,
            'flag_reasons': json.loads(self.flag_reasons) if self.flag_reasons else {},
            'error_count': self.error_count,
            'error_details': json.loads(self.error_details) if self.error_details else [],
            'use_real_data': self.use_real_data
        }
    
    def __repr__(self):
        """String representation for debugging."""
        enhancements = []
        if self.total_images_analyzed > 0:
            enhancements.append(f"{self.total_images_analyzed}img")
        if self.network_analyses_performed > 0:
            enhancements.append(f"{self.network_analyses_performed}net")
        
        enhancement_str = f" +{','.join(enhancements)}" if enhancements else ""
        return f'<MonitoringSession {self.id}: {self.session_type} - {self.total_flagged}/{self.total_articles_analyzed} flagged{enhancement_str}>'