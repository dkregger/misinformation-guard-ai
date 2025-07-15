from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create the database object
db = SQLAlchemy()

class FlaggedPost(db.Model):
    """
    This model represents a flagged post in our database.
    Each row in the database will be one flagged post.
    """
    
    # Primary key - unique ID for each post
    id = db.Column(db.Integer, primary_key=True)
    
    # The actual content of the post/tweet
    content = db.Column(db.Text, nullable=False)
    
    # Confidence score from our classifier (0.0 to 1.0)
    confidence = db.Column(db.Float, nullable=False)
    
    # Label from classifier (like "propaganda" or "reliable")
    label = db.Column(db.String(50), nullable=False)
    
    # URL where the post was found
    url = db.Column(db.String(255))
    
    # Source platform (twitter, news site, etc.)
    source = db.Column(db.String(50))
    
    # When we flagged this post
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """
        Convert this database record to a Python dictionary.
        This makes it easy to send as JSON to our React app.
        """
        return {
            'id': self.id,
            'content': self.content,
            'confidence': self.confidence,
            'label': self.label,
            'url': self.url,
            'source': self.source,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        """
        This defines how the object looks when printed.
        Useful for debugging.
        """
        return f'<FlaggedPost {self.id}: {self.label}>'