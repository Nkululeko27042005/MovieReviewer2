from datetime import datetime
from app import db
from enum import Enum

class ReportReason(Enum):
    SPAM = 'spam'
    HARASSMENT = 'harassment'
    HATE_SPEECH = 'hate_speech'
    FALSE_INFORMATION = 'false_information'
    COPYRIGHT = 'copyright'
    INAPPROPRIATE_CONTENT = 'inappropriate_content'
    SPOILERS_NO_WARNING = 'spoilers_no_warning'
    FAKE_REVIEW = 'fake_review'
    OTHER = 'other'

class ReportStatus(Enum):
    PENDING = 'pending'
    REVIEWING = 'reviewing'
    RESOLVED = 'resolved'
    DISMISSED = 'dismissed'

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who reported and what
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Optional specific content being reported
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    # Report details
    reason = db.Column(db.Enum(ReportReason), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Status
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING)
    
    # Admin handling
    handled_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])
    handled_by = db.relationship('User', foreign_keys=[handled_by_id])
    
    def resolve(self, admin_id, action_taken, notes=None):
        """Mark report as resolved"""
        self.status = ReportStatus.RESOLVED
        self.handled_by_id = admin_id
        self.admin_notes = notes
        self.resolved_at = datetime.utcnow()
        db.session.commit()
        
        # Increment report count on the reported user
        self.reported_user.increment_reports(self.reason.value)
        
        # Check if user should be deactivated
        if self.reported_user.check_deactivation_criteria():
            db.session.commit()
        
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'reporter_username': self.reporter.username if self.reporter else None,
            'reported_user_id': self.reported_user_id,
            'reported_username': self.reported_user.username if self.reported_user else None,
            'review_id': self.review_id,
            'comment_id': self.comment_id,
            'reason': self.reason.value if self.reason else None,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'handled_by_id': self.handled_by_id,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self):
        return f'<Report {self.id}: User {self.reported_user_id} reported by {self.reporter_id}>'