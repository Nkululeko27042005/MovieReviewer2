from app.models.comment import Comment
from app.models.review import Review
from app.services.notification_service import NotificationService
from app import db
from datetime import datetime

class CommentService:
    
    @staticmethod
    def create_comment(content, author_id, review_id, parent_comment_id=None,
                      has_emoji=False, has_gif=False, gif_url=None):
        """Create a new comment"""
        review = Review.query.get(review_id)
        if not review:
            return None, 'Review not found'
        
        comment = Comment(
            content=content,
            author_id=author_id,
            review_id=review_id,
            parent_comment_id=parent_comment_id,
            has_emoji=has_emoji,
            has_gif=has_gif,
            gif_url=gif_url
        )
        
        db.session.add(comment)
        
        # Update review comment count
        review.comments_count += 1
        
        # Update parent comment reply count if it's a reply
        if parent_comment_id:
            parent = Comment.query.get(parent_comment_id)
            if parent:
                parent.replies_count += 1
        
        db.session.commit()
        
        # Send notifications
        NotificationService.notify_comment_on_review(review, comment)
        
        return comment, 'Comment created successfully'
    
    @staticmethod
    def get_comments_by_review(review_id, page=1, per_page=30):
        """Get paginated comments for a review"""
        query = Comment.query.filter_by(
            review_id=review_id,
            parent_comment_id=None  # Only top-level comments
        ).order_by(Comment.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_replies(comment_id, page=1, per_page=20):
        """Get replies to a comment"""
        query = Comment.query.filter_by(parent_comment_id=comment_id).order_by(Comment.created_at)
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def delete_comment(comment_id, user_id, is_admin=False):
        """Delete a comment"""
        comment = Comment.query.get(comment_id)
        if not comment:
            return False, 'Comment not found'
        
        # Check permission
        if comment.author_id != user_id and not is_admin:
            return False, 'Permission denied'
        
        # Decrease counts
        review = Review.query.get(comment.review_id)
        if review:
            review.comments_count = max(0, review.comments_count - 1)
        
        if comment.parent_comment_id:
            parent = Comment.query.get(comment.parent_comment_id)
            if parent:
                parent.replies_count = max(0, parent.replies_count - 1)
        
        db.session.delete(comment)
        db.session.commit()
        return True, 'Comment deleted'
    
    @staticmethod
    def update_comment(comment_id, content, user_id, is_admin=False):
        """Update a comment"""
        comment = Comment.query.get(comment_id)
        if not comment:
            return None, 'Comment not found'
        
        if comment.author_id != user_id and not is_admin:
            return None, 'Permission denied'
        
        comment.content = content
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        return comment, 'Comment updated'

    @staticmethod
    def like_comment(comment_id, user_id):
        """Like a comment"""
        from app.models.comment import CommentReaction
        comment = Comment.query.get(comment_id)
        if not comment:
            return False, 'Comment not found'
        
        existing = CommentReaction.query.filter_by(user_id=user_id, comment_id=comment_id).first()
        if existing:
            return False, 'Comment already liked'
        
        reaction = CommentReaction(user_id=user_id, comment_id=comment_id, reaction_type='like')
        db.session.add(reaction)
        comment.likes_count += 1
        db.session.commit()
        return True, 'Comment liked successfully'