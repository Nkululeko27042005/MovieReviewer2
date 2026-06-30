from datetime import datetime
from flask_login import UserMixin
from app import db
from enum import Enum

class UserType(Enum):
    REGULAR = 'regular'
    REVIEWER = 'reviewer'
    ADMIN = 'admin'

class AccountStatus(Enum):
    ACTIVE = 'active'
    REPORT_LIMIT_REACHED = 'report_limit_reached'
    DEACTIVATED = 'deactivated'
    SUSPENDED = 'suspended'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Profile info
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    favorite_genres = db.Column(db.String(255), nullable=True)  # Comma-separated genre IDs
    
    # Account type and status
    user_type = db.Column(db.Enum(UserType), default=UserType.REGULAR, nullable=False)
    account_status = db.Column(db.Enum(AccountStatus), default=AccountStatus.ACTIVE)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Report tracking
    total_reports = db.Column(db.Integer, default=0)
    report_count_by_reason = db.Column(db.JSON, default=dict)  # Stores counts per reason
    
    # Deactivation info
    deactivated_at = db.Column(db.DateTime, nullable=True)
    deactivation_reason = db.Column(db.String(200), nullable=True)
    
    # Relationships
    reviews = db.relationship('Review', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes_given = db.relationship('UserLike', backref='user', lazy='dynamic', foreign_keys='UserLike.user_id')
    saves = db.relationship('UserSave', backref='user', lazy='dynamic')
    
    # Following relationships
    following = db.relationship('UserFollow', foreign_keys='UserFollow.follower_id', backref='follower', lazy='dynamic')
    followers = db.relationship('UserFollow', foreign_keys='UserFollow.followed_id', backref='followed', lazy='dynamic')
    
    # Notifications
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', foreign_keys='Notification.user_id')
    
    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    def can_create_reviews(self):
        return self.user_type in [UserType.REVIEWER, UserType.ADMIN] and self.account_status == AccountStatus.ACTIVE
    
    def is_active_account(self):
        return self.account_status == AccountStatus.ACTIVE
    
    def increment_reports(self, reason):
        """Increment report count for a specific reason"""
        if not self.report_count_by_reason:
            self.report_count_by_reason = {}
        
        self.report_count_by_reason[reason] = self.report_count_by_reason.get(reason, 0) + 1
        self.total_reports = sum(self.report_count_by_reason.values())
    
    def check_deactivation_criteria(self):
        """Check if user meets deactivation criteria"""
        from config import Config
        
        # Check for same reason reported 4 times
        for reason, count in self.report_count_by_reason.items():
            if count >= Config.MAX_REPORTS_SAME_REASON:
                self.account_status = AccountStatus.REPORT_LIMIT_REACHED
                self.deactivated_at = datetime.utcnow()
                self.deactivation_reason = f'Reported {count} times for: {reason}'
                return True
        
        # Check for 7 different reasons
        if len(self.report_count_by_reason) >= Config.MAX_REPORTS_DIFFERENT_REASONS:
            self.account_status = AccountStatus.REPORT_LIMIT_REACHED
            self.deactivated_at = datetime.utcnow()
            self.deactivation_reason = 'Reported for 7 different reasons'
            return True
        
        return False
    
    def follow(self, user):
        if not self.is_following(user):
            follow = UserFollow(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)
            db.session.commit()
            return True
        return False
    
    def unfollow(self, user):
        follow = UserFollow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()
            return True
        return False
    
    def is_following(self, user):
        return UserFollow.query.filter_by(follower_id=self.id, followed_id=user.id).first() is not None
    
    def like_review(self, review):
        existing = UserLike.query.filter_by(user_id=self.id, review_id=review.id).first()
        if not existing:
            like = UserLike(user_id=self.id, review_id=review.id)
            db.session.add(like)
            review.likes_count += 1
            db.session.commit()
            return True
        return False
    
    def unlike_review(self, review):
        like = UserLike.query.filter_by(user_id=self.id, review_id=review.id).first()
        if like:
            db.session.delete(like)
            review.likes_count = max(0, review.likes_count - 1)
            db.session.commit()
            return True
        return False
    
    def save_review(self, review):
        existing = UserSave.query.filter_by(user_id=self.id, review_id=review.id).first()
        if not existing:
            save = UserSave(user_id=self.id, review_id=review.id)
            db.session.add(save)
            db.session.commit()
            return True
        return False
    
    def unsave_review(self, review):
        save = UserSave.query.filter_by(user_id=self.id, review_id=review.id).first()
        if save:
            db.session.delete(save)
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'bio': self.bio,
            'profile_picture': self.profile_picture,
            'user_type': self.user_type.value if self.user_type else None,
            'account_status': self.account_status.value if self.account_status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_reviews': self.reviews.count(),
            'total_followers': self.followers.count(),
            'total_following': self.following.count(),
            'total_likes_received': sum([review.likes_count for review in self.reviews])
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserFollow(db.Model):
    __tablename__ = 'user_follows'
    
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),)

class UserFavoriteGenre(db.Model):
    __tablename__ = 'user_favorite_genres'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'genre_id', name='unique_user_genre'),)

class UserLike(db.Model):
    __tablename__ = 'user_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='unique_like'),)

class UserSave(db.Model):
    __tablename__ = 'user_saves'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='unique_save'),)

class UserNotificationPreference(db.Model):
    __tablename__ = 'user_notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    notify_on_follow = db.Column(db.Boolean, default=True)
    notify_on_like = db.Column(db.Boolean, default=True)
    notify_on_comment = db.Column(db.Boolean, default=True)
    notify_on_review_from_followed = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=False)