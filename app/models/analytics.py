from datetime import datetime, date
from app import db

class UserAnalytics(db.Model):
    """Daily aggregated analytics for each user"""
    __tablename__ = 'user_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    
    # Daily stats
    reviews_created = db.Column(db.Integer, default=0)
    comments_made = db.Column(db.Integer, default=0)
    likes_received = db.Column(db.Integer, default=0)
    likes_given = db.Column(db.Integer, default=0)
    new_followers = db.Column(db.Integer, default=0)
    profile_views = db.Column(db.Integer, default=0)
    
    # Cumulative totals (snapshot at end of day)
    total_reviews = db.Column(db.Integer, default=0)
    total_comments = db.Column(db.Integer, default=0)
    total_likes_received = db.Column(db.Integer, default=0)
    total_followers = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_daily'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'reviews_created': self.reviews_created,
            'comments_made': self.comments_made,
            'likes_received': self.likes_received,
            'likes_given': self.likes_given,
            'new_followers': self.new_followers,
            'profile_views': self.profile_views,
            'total_reviews': self.total_reviews,
            'total_comments': self.total_comments,
            'total_likes_received': self.total_likes_received,
            'total_followers': self.total_followers,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ReviewAnalytics(db.Model):
    """Analytics for individual reviews"""
    __tablename__ = 'review_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False, unique=True)
    
    # Stats that are updated in real-time via triggers/counts
    view_count = db.Column(db.Integer, default=0)
    unique_viewers = db.Column(db.Integer, default=0)  # Approximate using IP or user_id tracking
    avg_time_spent_seconds = db.Column(db.Float, default=0.0)
    
    # Engagement metrics
    like_rate = db.Column(db.Float, default=0.0)  # likes / views
    comment_rate = db.Column(db.Float, default=0.0)  # comments / views
    save_rate = db.Column(db.Float, default=0.0)  # saves / views
    
    # Time-based metrics
    peak_engagement_hour = db.Column(db.Integer, nullable=True)  # 0-23
    peak_engagement_day = db.Column(db.Integer, nullable=True)  # 0-6 (Monday=0)
    
    # Daily breakdown (stored as JSON for simplicity)
    daily_views = db.Column(db.JSON, default=dict)  # {'2024-01-01': 100, ...}
    daily_likes = db.Column(db.JSON, default=dict)
    daily_comments = db.Column(db.JSON, default=dict)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DailyAnalytics(db.Model):
    """Global daily analytics for the platform"""
    __tablename__ = 'daily_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    
    # Platform-wide daily metrics
    total_reviews = db.Column(db.Integer, default=0)
    total_comments = db.Column(db.Integer, default=0)
    total_likes = db.Column(db.Integer, default=0)
    total_new_users = db.Column(db.Integer, default=0)
    total_reports = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)  # Users who performed at least one action
    
    # Engagement rates
    avg_reviews_per_user = db.Column(db.Float, default=0.0)
    avg_comments_per_review = db.Column(db.Float, default=0.0)
    
    # Distribution
    review_genre_distribution = db.Column(db.JSON, default=dict)  # {'Action': 10, 'Drama': 5, ...}
    avg_rating_distribution = db.Column(db.JSON, default=dict)  # {'1': 0, '2': 0, ...}
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_reviews': self.total_reviews,
            'total_comments': self.total_comments,
            'total_likes': self.total_likes,
            'total_new_users': self.total_new_users,
            'total_reports': self.total_reports,
            'active_users': self.active_users,
            'avg_reviews_per_user': self.avg_reviews_per_user,
            'avg_comments_per_review': self.avg_comments_per_review,
            'review_genre_distribution': self.review_genre_distribution,
            'avg_rating_distribution': self.avg_rating_distribution,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }