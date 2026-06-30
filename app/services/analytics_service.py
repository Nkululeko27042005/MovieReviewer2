from datetime import date, datetime
from app import db

class AnalyticsService:
    """Service for handling analytics and statistics."""

    @staticmethod
    def _ensure_daily_analytics_table():
        """Create the daily analytics table if it does not exist."""
        from app.models.analytics import DailyAnalytics

        # Use SQLAlchemy inspector to check for table existence (Engine.has_table
        # is not available on modern SQLAlchemy Engine objects).
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        if not inspector.has_table(DailyAnalytics.__tablename__):
            DailyAnalytics.__table__.create(bind=db.engine, checkfirst=True)

    @staticmethod
    def _ensure_user_analytics_table():
        """Create the user analytics table if it does not exist."""
        from app.models.analytics import UserAnalytics
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        if not inspector.has_table(UserAnalytics.__tablename__):
            UserAnalytics.__table__.create(bind=db.engine, checkfirst=True)
    
    @staticmethod
    def get_review_statistics():
        """Get statistics about reviews."""
        from app.models.review import Review

        total_reviews = Review.query.count()
        average_rating = db.session.query(db.func.avg(Review.overall_rating)).scalar() or 0.0

        return {
            'total_reviews': total_reviews,
            'average_rating': float(round(average_rating, 2))
        }
    
    @staticmethod
    def get_user_statistics():
        """Get statistics about users."""
        from app.models.user import User

        total_users = User.query.count()
        active_users = User.query.filter(User.last_login != None).count()

        return {
            'total_users': total_users,
            'active_users': active_users
        }
    
    @staticmethod
    @staticmethod
    def _normalize_user_analytics_counters(analytics):
        """Ensure user analytics counter fields are initialized to integers."""
        for field in (
            'reviews_created',
            'comments_made',
            'likes_received',
            'likes_given',
            'new_followers',
            'profile_views',
            'total_reviews',
            'total_comments',
            'total_likes_received',
            'total_followers'
        ):
            if getattr(analytics, field) is None:
                setattr(analytics, field, 0)

    def update_user_daily_stats(user_id, activity_type):
        """Update aggregate daily stats for a user."""
        from app.models.analytics import UserAnalytics

        AnalyticsService._ensure_user_analytics_table()

        today = date.today()
        analytics = UserAnalytics.query.filter_by(user_id=user_id, date=today).first()
        if not analytics:
            analytics = UserAnalytics(user_id=user_id, date=today)
            db.session.add(analytics)

        AnalyticsService._normalize_user_analytics_counters(analytics)

        if activity_type == 'profile_view':
            analytics.profile_views += 1
        elif activity_type == 'review_created':
            analytics.reviews_created += 1
        elif activity_type == 'comment_made':
            analytics.comments_made += 1
        elif activity_type == 'like_received':
            analytics.likes_received += 1
        elif activity_type == 'like_given':
            analytics.likes_given += 1
        elif activity_type == 'new_follower':
            analytics.new_followers += 1
        
        db.session.commit()
        return analytics.to_dict()

    @staticmethod
    def get_user_analytics_summary(user_id, days=30):
        """Get a summary of user analytics for the requested time window."""
        from datetime import timedelta
        from app.models.analytics import UserAnalytics

        AnalyticsService._ensure_user_analytics_table()

        end_date = date.today()
        start_date = end_date - timedelta(days=max(days - 1, 0))

        rows = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.date >= start_date,
            UserAnalytics.date <= end_date
        ).order_by(UserAnalytics.date.desc()).all()

        analytics = [row.to_dict() for row in rows]
        summary = {
            'reviews_created': sum(row['reviews_created'] for row in analytics),
            'comments_made': sum(row['comments_made'] for row in analytics),
            'likes_received': sum(row['likes_received'] for row in analytics),
            'likes_given': sum(row['likes_given'] for row in analytics),
            'new_followers': sum(row['new_followers'] for row in analytics),
            'profile_views': sum(row['profile_views'] for row in analytics)
        }

        return {
            'user_id': user_id,
            'days': len(analytics),
            'analytics': analytics,
            'summary': summary
        }

    @staticmethod
    def get_global_daily_analytics(date_obj):
        """Return stored daily analytics for a specific date."""
        from app.models.analytics import DailyAnalytics

        AnalyticsService._ensure_daily_analytics_table()

        analytics = DailyAnalytics.query.filter_by(date=date_obj).first()
        if not analytics:
            return None
        return analytics.to_dict()

    @staticmethod
    def calculate_global_daily_analytics(date_obj):
        """Calculate or update the platform-wide daily analytics."""
        from app.models.analytics import DailyAnalytics
        from app.models.comment import Comment
        from app.models.report import Report
        from app.models.review import Review, ReviewGenre
        from app.models.user import User, UserLike

        AnalyticsService._ensure_daily_analytics_table()

        total_reviews = Review.query.filter(db.func.date(Review.created_at) == date_obj).count()
        total_comments = Comment.query.filter(db.func.date(Comment.created_at) == date_obj).count()
        total_likes = UserLike.query.filter(db.func.date(UserLike.created_at) == date_obj).count()
        total_new_users = User.query.filter(db.func.date(User.created_at) == date_obj).count()
        total_reports = Report.query.filter(db.func.date(Report.created_at) == date_obj).count()

        review_genre_distribution = {}
        review_genres = ReviewGenre.query.join(Review).filter(db.func.date(Review.created_at) == date_obj).all()
        for review_genre in review_genres:
            if review_genre.genre:
                name = review_genre.genre.name
                review_genre_distribution[name] = review_genre_distribution.get(name, 0) + 1

        avg_rating_distribution = {}
        reviews_on_date = Review.query.filter(db.func.date(Review.created_at) == date_obj).all()
        for review in reviews_on_date:
            if review.overall_rating is None:
                continue
            rating_key = str(int(round(review.overall_rating)))
            avg_rating_distribution[rating_key] = avg_rating_distribution.get(rating_key, 0) + 1

        active_user_ids = set()
        review_user_ids = db.session.query(Review.author_id).filter(db.func.date(Review.created_at) == date_obj).distinct()
        comment_user_ids = db.session.query(Comment.author_id).filter(db.func.date(Comment.created_at) == date_obj).distinct()
        like_user_ids = db.session.query(UserLike.user_id).filter(db.func.date(UserLike.created_at) == date_obj).distinct()
        report_user_ids = db.session.query(Report.reporter_id).filter(db.func.date(Report.created_at) == date_obj).distinct()

        for row in review_user_ids:
            active_user_ids.add(row[0])
        for row in comment_user_ids:
            active_user_ids.add(row[0])
        for row in like_user_ids:
            active_user_ids.add(row[0])
        for row in report_user_ids:
            active_user_ids.add(row[0])

        active_users = len(active_user_ids)
        avg_reviews_per_user = float(total_reviews) / active_users if active_users else 0.0
        avg_comments_per_review = float(total_comments) / total_reviews if total_reviews else 0.0

        analytics = DailyAnalytics.query.filter_by(date=date_obj).first()
        if not analytics:
            analytics = DailyAnalytics(date=date_obj)
            db.session.add(analytics)

        analytics.total_reviews = total_reviews
        analytics.total_comments = total_comments
        analytics.total_likes = total_likes
        analytics.total_new_users = total_new_users
        analytics.total_reports = total_reports
        analytics.active_users = active_users
        analytics.avg_reviews_per_user = avg_reviews_per_user
        analytics.avg_comments_per_review = avg_comments_per_review
        analytics.review_genre_distribution = review_genre_distribution
        analytics.avg_rating_distribution = avg_rating_distribution
        analytics.created_at = datetime.utcnow()

        db.session.commit()
        return analytics

    @staticmethod
    def track_user_activity(user_id, activity_type):
        """Track user activity for analytics."""
        return AnalyticsService.update_user_daily_stats(user_id, activity_type)

    @staticmethod
    def track_review_view(review_id, user_id=None):
        """Track that a review was viewed (stub for tests)."""
        # no-op for now; implement analytics logging later
        return None
