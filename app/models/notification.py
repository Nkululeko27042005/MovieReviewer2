from datetime import datetime
from app import db
from enum import Enum

class NotificationType(Enum):
    FOLLOW = 'follow'
    LIKE = 'like'
    COMMENT = 'comment'
    NEW_REVIEW_FROM_FOLLOWED = 'new_review_from_followed'
    REVIEW_MENTION = 'review_mention'
    REPORT_RESOLVED = 'report_resolved'
    ACCOUNT_STATUS_CHANGE = 'account_status_change'

class NotificationStatus(Enum):
    UNREAD = 'unread'
    READ = 'read'
    ARCHIVED = 'archived'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    
    # Content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Related objects (for linking)
    source_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    # Metadata
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    metadata_json = db.Column(db.JSON, default=dict)  # Additional data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    source_user = db.relationship('User', foreign_keys=[source_user_id])
    
    def mark_as_read(self):
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.notification_type.value if self.notification_type else None,
            'title': self.title,
            'message': self.message,
            'status': self.status.value if self.status else None,
            'source_user_id': self.source_user_id,
            'source_username': self.source_user.username if self.source_user else None,
            'review_id': self.review_id,
            'comment_id': self.comment_id,
            'metadata': self.metadata_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.notification_type}>'