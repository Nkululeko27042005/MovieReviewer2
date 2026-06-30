from app.models.review import Review, GoodMoment, BadMoment, ReviewGenre, ReviewRating
from app.models.user import UserLike, UserSave
from app.models.genre import Genre
from app.services.file_service import FileService
from app.services.notification_service import NotificationService
from app import db
from datetime import datetime
from sqlalchemy import or_, and_, desc

class ReviewService:
    
    @staticmethod
    def create_review(author_id, data, good_moments_data=None, bad_moments_data=None, 
                     review_poster=None, movie_poster=None, genres=None):
        """Create a new review"""
        
        # Create review object
        review = Review(
            title=data.get('title'),
            movie_name=data.get('movie_name'),
            overall_rating=float(data.get('overall_rating')),
            overall_thoughts=data.get('overall_thoughts'),
            acting_rating=float(data.get('acting_rating')),
            cast_selection_rating=float(data.get('cast_selection_rating')),
            pacing_rating=float(data.get('pacing_rating')),
            plot_rating=float(data.get('plot_rating')),
            has_spoilers=data.get('has_spoilers', False),
            author_id=author_id
        )
        
        # Save posters
        if review_poster and review_poster.filename:
            poster_path = FileService.save_file(review_poster, 'app/static/uploads/review_posters')
            if poster_path:
                review.review_poster_url = FileService.get_url_path(poster_path)
        
        if movie_poster and movie_poster.filename:
            poster_path = FileService.save_file(movie_poster, 'app/static/uploads/review_posters')
            if poster_path:
                review.movie_poster_url = FileService.get_url_path(poster_path)
        
        db.session.add(review)
        db.session.flush()
        
        # Add genres
        if genres:
            for genre_id in genres:
                if genre_id:
                    review_genre = ReviewGenre(review_id=review.id, genre_id=int(genre_id))
                    db.session.add(review_genre)
        
        # Add good moments
        if good_moments_data:
            for moment_data in good_moments_data:
                moment = GoodMoment(
                    review_id=review.id,
                    description=moment_data.get('description'),
                    scene_description=moment_data.get('scene_description'),
                    order_index=moment_data.get('order_index', 0)
                )
                
                # Handle multiple images
                if moment_data.get('images'):
                    images = moment_data.get('images')
                    if isinstance(images, list):
                        image_paths = FileService.save_multiple_files(images, 'app/static/uploads/good_moments')
                        moment.image_urls = [FileService.get_url_path(p) for p in image_paths if p]
                    else:
                        path = FileService.save_file(images, 'app/static/uploads/good_moments')
                        if path:
                            moment.image_urls = [FileService.get_url_path(path)]
                
                db.session.add(moment)
        
        # Add bad moments
        if bad_moments_data:
            for moment_data in bad_moments_data:
                moment = BadMoment(
                    review_id=review.id,
                    description=moment_data.get('description'),
                    scene_description=moment_data.get('scene_description'),
                    order_index=moment_data.get('order_index', 0)
                )
                
                if moment_data.get('images'):
                    images = moment_data.get('images')
                    if isinstance(images, list):
                        image_paths = FileService.save_multiple_files(images, 'app/static/uploads/bad_moments')
                        moment.image_urls = [FileService.get_url_path(p) for p in image_paths if p]
                    else:
                        path = FileService.save_file(images, 'app/static/uploads/bad_moments')
                        if path:
                            moment.image_urls = [FileService.get_url_path(path)]
                
                db.session.add(moment)
        
        db.session.commit()
        
        # Notify followers
        NotificationService.notify_followers_of_new_review(review)
        
        return review
    
    @staticmethod
    def get_review_by_id(review_id, increment_view=True):
        """Get a review by ID with optional view increment"""
        review = Review.query.get(review_id)
        if review and increment_view:
            review.views_count += 1
            db.session.commit()
        return review
    
    @staticmethod
    def update_review(review_id, data, good_moments_data=None, bad_moments_data=None,
                     review_poster=None, movie_poster=None, genres=None):
        """Update an existing review"""
        review = Review.query.get(review_id)
        if not review:
            return None, 'Review not found'
        
        # Update fields
        if 'title' in data:
            review.title = data['title']
        if 'movie_name' in data:
            review.movie_name = data['movie_name']
        if 'overall_rating' in data:
            review.overall_rating = float(data['overall_rating'])
        if 'overall_thoughts' in data:
            review.overall_thoughts = data['overall_thoughts']
        if 'acting_rating' in data:
            review.acting_rating = float(data['acting_rating'])
        if 'cast_selection_rating' in data:
            review.cast_selection_rating = float(data['cast_selection_rating'])
        if 'pacing_rating' in data:
            review.pacing_rating = float(data['pacing_rating'])
        if 'plot_rating' in data:
            review.plot_rating = float(data['plot_rating'])
        if 'has_spoilers' in data:
            review.has_spoilers = data['has_spoilers']
        
        review.updated_at = datetime.utcnow()
        
        # Update posters
        if review_poster and review_poster.filename:
            # Delete old poster if exists
            if review.review_poster_url:
                FileService.delete_file(review.review_poster_url)
            poster_path = FileService.save_file(review_poster, 'app/static/uploads/review_posters')
            if poster_path:
                review.review_poster_url = FileService.get_url_path(poster_path)
        
        if movie_poster and movie_poster.filename:
            if review.movie_poster_url:
                FileService.delete_file(review.movie_poster_url)
            poster_path = FileService.save_file(movie_poster, 'app/static/uploads/review_posters')
            if poster_path:
                review.movie_poster_url = FileService.get_url_path(poster_path)
        
        # Update genres
        if genres is not None:
            # Remove existing genres
            ReviewGenre.query.filter_by(review_id=review.id).delete()
            for genre_id in genres:
                if genre_id:
                    review_genre = ReviewGenre(review_id=review.id, genre_id=int(genre_id))
                    db.session.add(review_genre)
        
        # Update good moments (remove old ones)
        if good_moments_data is not None:
            # Delete old moments and their images
            for old_moment in review.good_moments:
                if old_moment.image_urls:
                    FileService.delete_multiple_files(old_moment.image_urls)
            GoodMoment.query.filter_by(review_id=review.id).delete()
            
            # Add new moments
            for moment_data in good_moments_data:
                moment = GoodMoment(
                    review_id=review.id,
                    description=moment_data.get('description'),
                    scene_description=moment_data.get('scene_description'),
                    order_index=moment_data.get('order_index', 0)
                )
                if moment_data.get('images'):
                    images = moment_data.get('images')
                    if isinstance(images, list):
                        image_paths = FileService.save_multiple_files(images, 'app/static/uploads/good_moments')
                        moment.image_urls = [FileService.get_url_path(p) for p in image_paths if p]
                    else:
                        path = FileService.save_file(images, 'app/static/uploads/good_moments')
                        if path:
                            moment.image_urls = [FileService.get_url_path(path)]
                db.session.add(moment)
        
        # Update bad moments
        if bad_moments_data is not None:
            for old_moment in review.bad_moments:
                if old_moment.image_urls:
                    FileService.delete_multiple_files(old_moment.image_urls)
            BadMoment.query.filter_by(review_id=review.id).delete()
            
            for moment_data in bad_moments_data:
                moment = BadMoment(
                    review_id=review.id,
                    description=moment_data.get('description'),
                    scene_description=moment_data.get('scene_description'),
                    order_index=moment_data.get('order_index', 0)
                )
                if moment_data.get('images'):
                    images = moment_data.get('images')
                    if isinstance(images, list):
                        image_paths = FileService.save_multiple_files(images, 'app/static/uploads/bad_moments')
                        moment.image_urls = [FileService.get_url_path(p) for p in image_paths if p]
                    else:
                        path = FileService.save_file(images, 'app/static/uploads/bad_moments')
                        if path:
                            moment.image_urls = [FileService.get_url_path(path)]
                db.session.add(moment)
        
        db.session.commit()
        return review, 'Review updated successfully'
    
    @staticmethod
    def delete_review(review_id):
        """Delete a review and all associated files"""
        review = Review.query.get(review_id)
        if not review:
            return False, 'Review not found'
        
        # Delete images
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
        
        # Delete review (cascade will handle related records)
        db.session.delete(review)
        db.session.commit()
        return True, 'Review deleted successfully'
    
    @staticmethod
    def get_reviews_by_user(user_id, page=1, per_page=20, sort_by='newest'):
        """Get paginated reviews by user"""
        query = Review.query.filter_by(author_id=user_id, is_published=True)
        
        if sort_by == 'newest':
            query = query.order_by(desc(Review.published_at))
        elif sort_by == 'oldest':
            query = query.order_by(Review.published_at)
        elif sort_by == 'top_rated':
            query = query.order_by(desc(Review.overall_rating))
        elif sort_by == 'most_liked':
            query = query.order_by(desc(Review.likes_count))
        elif sort_by == 'most_commented':
            query = query.order_by(desc(Review.comments_count))
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_feed(user, page=1, per_page=20, sort_by='newest'):
        """Get personalized feed for a user"""
        # Get user's favorite genres
        from app.models.user import UserFavoriteGenre
        favorite_genres = UserFavoriteGenre.query.filter_by(user_id=user.id).all()
        favorite_genre_ids = [fg.genre_id for fg in favorite_genres]
        
        # Build query
        query = Review.query.filter_by(is_published=True)
        filters = []

        if favorite_genre_ids:
            # Get reviews from favorite genres
            genre_reviews = db.session.query(ReviewGenre.review_id).filter(
                ReviewGenre.genre_id.in_(favorite_genre_ids)
            ).subquery()
            filters.append(Review.id.in_(genre_reviews))

        # Also include reviews from followed users
        followed_ids = [f.followed_id for f in user.following]
        if followed_ids:
            filters.append(Review.author_id.in_(followed_ids))

        if filters:
            query = query.filter(or_(*filters))
        if sort_by == 'newest':
            query = query.order_by(desc(Review.published_at))
        elif sort_by == 'most_viewed':
            query = query.order_by(desc(Review.views_count))
        elif sort_by == 'most_liked':
            query = query.order_by(desc(Review.likes_count))
        elif sort_by == 'top_rated':
            query = query.order_by(desc(Review.overall_rating))
        else:
            query = query.order_by(desc(Review.published_at))
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def like_review(user, review_id):
        """Like a review"""
        review = Review.query.get(review_id)
        if not review:
            return False, 'Review not found'
        
        if user.like_review(review):
            return True, 'Review liked'
        return False, 'Already liked'
    
    @staticmethod
    def unlike_review(user, review_id):
        """Unlike a review"""
        review = Review.query.get(review_id)
        if not review:
            return False, 'Review not found'
        
        if user.unlike_review(review):
            return True, 'Review unliked'
        return False, 'Not liked'
    
    @staticmethod
    def save_review(user, review_id):
        """Save/favorite a review"""
        review = Review.query.get(review_id)
        if not review:
            return False, 'Review not found'
        
        if user.save_review(review):
            return True, 'Review saved'
        return False, 'Already saved'
    
    @staticmethod
    def unsave_review(user, review_id):
        """Unsave a review"""
        review = Review.query.get(review_id)
        if not review:
            return False, 'Review not found'
        
        if user.unsave_review(review):
            return True, 'Review unsaved'
        return False, 'Not saved'
    
    @staticmethod
    def search_reviews(query_string, genre_ids=None, min_rating=None, max_rating=None,
                      has_spoilers=None, page=1, per_page=20):
        """Search reviews with filters"""
        query = Review.query.filter_by(is_published=True)
        
        if query_string:
            query = query.filter(
                or_(
                    Review.movie_name.ilike(f'%{query_string}%'),
                    Review.title.ilike(f'%{query_string}%'),
                    Review.overall_thoughts.ilike(f'%{query_string}%')
                )
            )
        
        if genre_ids:
            genre_reviews = db.session.query(ReviewGenre.review_id).filter(
                ReviewGenre.genre_id.in_(genre_ids)
            ).subquery()
            query = query.filter(Review.id.in_(genre_reviews))
        
        if min_rating is not None:
            query = query.filter(Review.overall_rating >= float(min_rating))
        
        if max_rating is not None:
            query = query.filter(Review.overall_rating <= float(max_rating))
        
        if has_spoilers is not None:
            query = query.filter(Review.has_spoilers == has_spoilers)
        
        query = query.order_by(desc(Review.published_at))
        return query.paginate(page=page, per_page=per_page, error_out=False)