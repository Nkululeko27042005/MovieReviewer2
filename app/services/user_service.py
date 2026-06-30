from flask_bcrypt import generate_password_hash, check_password_hash
from app.models.user import User, UserFollow, UserFavoriteGenre, AccountStatus, UserType
from app.models.genre import Genre
from app.models.review import Review
from app.services.file_service import FileService
from app import db
from datetime import datetime

class UserService:
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def update_profile(user, data, profile_picture=None):
        """Update user profile"""
        if 'username' in data and data['username'] != user.username:
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user.id:
                return False, 'Username already taken'
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return False, 'Email already registered'
            user.email = data['email']
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if profile_picture and profile_picture.filename:
            if user.profile_picture:
                FileService.delete_file(user.profile_picture)
            pic_path = FileService.save_file(profile_picture, 'app/static/uploads/profiles')
            if pic_path:
                user.profile_picture = FileService.get_url_path(pic_path)
        
        if 'favorite_genres' in data:
            # Clear existing favorites
            UserFavoriteGenre.query.filter_by(user_id=user.id).delete()
            
            # Add new favorites
            if data['favorite_genres']:
                genre_names = [g.strip() for g in data['favorite_genres'].split(',') if g.strip()]
                saved_genre_names = []
                for genre_name in genre_names:
                    genre = Genre.query.filter_by(name=genre_name).first()
                    if genre:
                        fav = UserFavoriteGenre(user_id=user.id, genre_id=genre.id)
                        db.session.add(fav)
                        saved_genre_names.append(genre.name)
                user.favorite_genres = ", ".join(saved_genre_names)
            else:
                user.favorite_genres = ""
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return True, 'Profile updated successfully'
    
    @staticmethod
    def change_password(user, current_password, new_password):
        """Change user password"""
        if not check_password_hash(user.password_hash, current_password):
            return False, 'Current password is incorrect'
        
        user.password_hash = generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        return True, 'Password changed successfully'
    
    @staticmethod
    def delete_user_account(user):
        """Delete user account and associated data"""
        # Delete profile picture
        if user.profile_picture:
            FileService.delete_file(user.profile_picture)
        
        # Delete user's reviews (cascade will handle images)
        for review in user.reviews:
            if review.review_poster_url:
                FileService.delete_file(review.review_poster_url)
            if review.movie_poster_url:
                FileService.delete_file(review.movie_poster_url)
            for moment in review.good_moments:
                if moment.image_urls:
                    FileService.delete_multiple_files(moment.image_urls)
            for moment in review.bad_moments:
                if moment.image_urls:
                    FileService.delete_multiple_files(moment.image_urls)
        
        db.session.delete(user)
        db.session.commit()
        return True, 'Account deleted successfully'
    
    @staticmethod
    def follow_user(follower, followee_id):
        """Follow another user"""
        followee = User.query.get(followee_id)
        if not followee:
            return False, 'User not found'
        
        if follower.id == followee.id:
            return False, 'Cannot follow yourself'
        
        if follower.follow(followee):
            return True, f'Now following {followee.username}'
        return False, 'Already following'
    
    @staticmethod
    def unfollow_user(follower, followee_id):
        """Unfollow a user"""
        followee = User.query.get(followee_id)
        if not followee:
            return False, 'User not found'
        
        if follower.unfollow(followee):
            return True, f'Unfollowed {followee.username}'
        return False, 'Not following'
    
    @staticmethod
    def get_followers(user_id, page=1, per_page=20):
        """Get paginated list of followers"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        query = User.query.join(UserFollow, UserFollow.follower_id == User.id).filter(
            UserFollow.followed_id == user_id
        )
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_following(user_id, page=1, per_page=20):
        """Get paginated list of users being followed"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        query = User.query.join(UserFollow, UserFollow.followed_id == User.id).filter(
            UserFollow.follower_id == user_id
        )
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_saved_reviews(user, page=1, per_page=20):
        """Get paginated list of saved reviews"""
        from app.models.review import Review
        saved_review_ids = [save.review_id for save in user.saves]
        query = Review.query.filter(Review.id.in_(saved_review_ids), Review.is_published == True)
        query = query.order_by(Review.published_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_user_stats(user_id):
        """Get comprehensive user statistics"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        reviews = user.reviews
        total_likes_received = sum([r.likes_count for r in reviews])
        total_comments_received = sum([r.comments_count for r in reviews])
        total_saves = sum([r.saves_count for r in reviews])
        total_views = sum([r.views_count for r in reviews])
        
        # Average rating
        if reviews.count() > 0:
            avg_rating = sum([r.overall_rating for r in reviews]) / reviews.count()
        else:
            avg_rating = 0
        
        # Top reviewed genre
        from app.models.review import ReviewGenre
        genre_counts = db.session.query(
            ReviewGenre.genre_id, db.func.count(ReviewGenre.review_id)
        ).join(Review).filter(Review.author_id == user_id).group_by(
            ReviewGenre.genre_id
        ).order_by(db.func.count(ReviewGenre.review_id).desc()).first()
        
        top_genre = None
        if genre_counts:
            genre = Genre.query.get(genre_counts[0])
            top_genre = genre.name if genre else None
        
        return {
            'total_reviews': reviews.count(),
            'total_likes_received': total_likes_received,
            'total_comments_received': total_comments_received,
            'total_saves': total_saves,
            'total_views': total_views,
            'average_rating': round(avg_rating, 2),
            'top_genre': top_genre,
            'total_followers': user.followers.count(),
            'total_following': user.following.count(),
            'account_age_days': (datetime.utcnow() - user.created_at).days,
            'reviews_this_month': reviews.filter(
                Review.created_at >= datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
            ).count(),
            'engagement_rate': total_likes_received / reviews.count() if reviews.count() > 0 else 0
        }