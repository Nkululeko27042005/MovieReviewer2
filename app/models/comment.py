from datetime import datetime
from app import db

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Relationships
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # For nested replies
    
    # Stats
    likes_count = db.Column(db.Integer, default=0)
    replies_count = db.Column(db.Integer, default=0)
    
    # Rich content
    has_emoji = db.Column(db.Boolean, default=False)
    has_gif = db.Column(db.Boolean, default=False)
    gif_url = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships for reactions/likes
    reactions = db.relationship('CommentReaction', backref='comment', lazy='dynamic', cascade='all, delete-orphan')
    
    # Self-referential for replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author_id': self.author_id,
            'author_username': self.author.username if self.author else None,
            'review_id': self.review_id,
            'parent_comment_id': self.parent_comment_id,
            'likes_count': self.likes_count,
            'replies_count': self.replies_count,
            'has_emoji': self.has_emoji,
            'has_gif': self.has_gif,
            'gif_url': self.gif_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CommentReaction(db.Model):
    """Tracks reactions (like, love, laugh, etc.) on comments"""
    __tablename__ = 'comment_reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # 'like', 'love', 'laugh', 'wow', 'sad', 'angry'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_comment_reaction'),)