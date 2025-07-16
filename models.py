"""
Database models for the misinformation detection system.

This file defines the database schema for storing flagged content
and monitoring session performance metrics.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Create the database object - this will be initialized by the Flask app
db = SQLAlchemy()

class FlaggedPost(db.Model):
    """
    Model for storing flagged social media posts and news articles.
    
    Each record represents one piece of content that was flagged
    by the misinformation detection system.
    """
    
    # Primary key - unique identifier for each flagged post
    id = db.Column(db.Integer, primary_key=True)
    
    # Content information
    content = db.Column(db.Text, nullable=False, comment="The actual text content")
    url = db.Column(db.String(255), comment="URL where content was found")
    source = db.Column(db.String(50), comment="Platform: twitter, news, etc.")
    username = db.Column(db.String(100), comment="Author username or news source")
    
    # Classification results
    confidence = db.Column(db.Float, nullable=False, comment="AI confidence score 0.0-1.0")
    label = db.Column(db.String(50), nullable=False, comment="Classification: propaganda, toxic, reliable")
    
    # Bot detection results (for social media posts)
    is_bot = db.Column(db.Boolean, default=False, comment="True if user appears to be a bot")
    bot_confidence = db.Column(db.Float, default=0.0, comment="Bot detection confidence 0.0-1.0")
    bot_reasons = db.Column(db.Text, comment="JSON list of bot indicators")
    
    # Monitoring session link
    session_id = db.Column(db.Integer, db.ForeignKey('monitoring_session.id'), 
                          comment="Links to the monitoring session that found this")
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, 
                         comment="When this content was flagged")
    
    def to_dict(self):
        """
        Convert database record to dictionary for JSON API responses.
        
        Returns:
            dict: All post data in JSON-serializable format
        """
        return {
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
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        """String representation for debugging."""
        bot_indicator = " [BOT]" if self.is_bot else ""
        return f'<FlaggedPost {self.id}: {self.label}{bot_indicator}>'


class MonitoringSession(db.Model):
    """
    Model for tracking monitoring session performance metrics.
    
    Each record represents one run of the monitoring system,
    with comprehensive performance and error tracking.
    """
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Session metadata
    session_type = db.Column(db.String(20), nullable=False, 
                           comment="Type: twitter, news, or both")
    start_time = db.Column(db.DateTime, default=datetime.utcnow,
                          comment="When monitoring started")
    end_time = db.Column(db.DateTime, comment="When monitoring completed")
    duration_seconds = db.Column(db.Float, comment="Total processing time")
    use_real_data = db.Column(db.Boolean, default=False,
                             comment="True if using real data vs mock data")
    
    # Content processing metrics
    total_articles_attempted = db.Column(db.Integer, default=0,
                                       comment="Number of articles/posts attempted to scrape")
    total_articles_successfully_scraped = db.Column(db.Integer, default=0,
                                                   comment="Number successfully downloaded")
    total_articles_analyzed = db.Column(db.Integer, default=0,
                                      comment="Number analyzed by AI classifier")
    total_flagged = db.Column(db.Integer, default=0,
                            comment="Number flagged as problematic")
    
    # Performance rates
    scraping_success_rate = db.Column(db.Float, default=0.0,
                                    comment="Percentage of successful scrapes")
    flagging_rate = db.Column(db.Float, default=0.0,
                            comment="Percentage of content flagged")
    
    # Source performance (stored as JSON strings)
    sources_attempted = db.Column(db.Text, comment="JSON: {domain: count} of attempted scrapes")
    sources_successful = db.Column(db.Text, comment="JSON: {domain: count} of successful scrapes")
    
    # Content classification breakdown
    propaganda_count = db.Column(db.Integer, default=0, comment="Posts classified as propaganda")
    toxic_count = db.Column(db.Integer, default=0, comment="Posts classified as toxic")
    bot_count = db.Column(db.Integer, default=0, comment="Posts from suspected bots")
    reliable_count = db.Column(db.Integer, default=0, comment="Posts classified as reliable")
    
    # Flag reason breakdown (JSON string)
    flag_reasons = db.Column(db.Text, comment="JSON: {reason: count} of why posts were flagged")
    
    # Error tracking
    error_count = db.Column(db.Integer, default=0, comment="Total errors encountered")
    error_details = db.Column(db.Text, comment="JSON: List of error messages with timestamps")
    
    # Relationship to flagged posts
    flagged_posts = db.relationship('FlaggedPost', backref='session', lazy=True,
                                   cascade="all, delete-orphan")
    
    def to_dict(self):
        """
        Convert database record to dictionary for JSON API responses.
        
        Returns:
            dict: All session data with JSON fields parsed
        """
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
            'scraping_success_rate': self.scraping_success_rate,
            'flagging_rate': self.flagging_rate,
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
        return f'<MonitoringSession {self.id}: {self.session_type} - {self.total_flagged}/{self.total_articles_analyzed} flagged>'