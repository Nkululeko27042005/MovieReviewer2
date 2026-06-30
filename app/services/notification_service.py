from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.user import User, UserFollow, UserNotificationPreference
from app import db
from datetime import datetime

class NotificationService:
    
    @staticmethod
    def create_notification(user_id, notification_type, title, message, 
                           source_user_id=None, review_id=None, comment_id=None, 
                           metadata=None):
        """Create a notification for a user"""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            source_user_id=source_user_id,
            review_id=review_id,
            comment_id=comment_id,
            metadata_json=metadata or {}
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def notify_followers_of_new_review(review):
        """Notify all followers of a user about a new review"""
        # Get all followers
        followers = UserFollow.query.filter_by(followed_id=review.author_id).all()
        
        for follow in followers:
            follower_id = follow.follower_id
            
            # Check notification preference
            pref = UserNotificationPreference.query.filter_by(user_id=follower_id).first()
            if pref and not pref.notify_on_review_from_followed:
                continue
            
            # Don't notify if it's the author's own post (shouldn't happen, but just in case)
            if follower_id == review.author_id:
                continue
            
            notification = Notification(
                user_id=follower_id,
                notification_type=NotificationType.NEW_REVIEW_FROM_FOLLOWED,
                title=f'New review from {review.author.username}',
                message=f'{review.author.username} just posted a review of "{review.movie_name}"',
                source_user_id=review.author_id,
                review_id=review.id
            )
            db.session.add(notification)
        
        db.session.commit()
    
    @staticmethod
    def notify_comment_on_review(review, comment):
        """Notify review author when someone comments"""
        # Don't notify if it's your own comment
        if comment.author_id == review.author_id:
            return
        
        # Check notification preference
        pref = UserNotificationPreference.query.filter_by(user_id=review.author_id).first()
        if pref and not pref.notify_on_comment:
            return
        
        notification = Notification(
            user_id=review.author_id,
            notification_type=NotificationType.COMMENT,
            title=f'New comment on your review',
            message=f'{comment.author.username} commented on your review of "{review.movie_name}"',
            source_user_id=comment.author_id,
            review_id=review.id,
            comment_id=comment.id
        )
        db.session.add(notification)
        db.session.commit()
    
    @staticmethod
    def notify_like_on_review(review, liker):
        """Notify review author when someone likes their review"""
        # Don't notify if it's your own like
        if liker.id == review.author_id:
            return
        
        # Check notification preference
        pref = UserNotificationPreference.query.filter_by(user_id=review.author_id).first()
        if pref and not pref.notify_on_like:
            return
        
        notification = Notification(
            user_id=review.author_id,
            notification_type=NotificationType.LIKE,
            title=f'New like on your review',
            message=f'{liker.username} liked your review of "{review.movie_name}"',
            source_user_id=liker.id,
            review_id=review.id
        )
        db.session.add(notification)
        db.session.commit()
    
    @staticmethod
    def notify_follow(followed_user, follower):
        """Notify when someone follows you"""
        if isinstance(followed_user, int):
            followed_user = User.query.get(followed_user)
        if isinstance(follower, int):
            follower = User.query.get(follower)

        if not followed_user or not follower:
            return

        # Don't notify if following yourself
        if follower.id == followed_user.id:
            return
        
        # Check notification preference
        pref = UserNotificationPreference.query.filter_by(user_id=followed_user.id).first()
        if pref and not pref.notify_on_follow:
            return
        
        notification = Notification(
            user_id=followed_user.id,
            notification_type=NotificationType.FOLLOW,
            title=f'New follower',
            message=f'{follower.username} started following you',
            source_user_id=follower.id
        )
        db.session.add(notification)
        db.session.commit()
    
    @staticmethod
    def get_user_notifications(user_id, status=None, limit=50, offset=0):
        """Get notifications for a user"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if status == 'unread':
            query = query.filter_by(status=NotificationStatus.UNREAD)
        elif status == 'read':
            query = query.filter_by(status=NotificationStatus.READ)
        
        query = query.order_by(Notification.created_at.desc())
        return query.limit(limit).offset(offset).all()
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        return Notification.query.filter_by(
            user_id=user_id,
            status=NotificationStatus.UNREAD
        ).count()
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read"""
        notifications = Notification.query.filter_by(
            user_id=user_id,
            status=NotificationStatus.UNREAD
        ).all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return len(notifications)