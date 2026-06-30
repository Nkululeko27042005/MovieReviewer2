from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import reviews_bp
from app.services.review_service import ReviewService
from app.services.comment_service import CommentService
from app.services.analytics_service import AnalyticsService
from app.forms.review_forms import ReviewForm
from app.forms.comment_forms import CommentForm
from config import Config

@reviews_bp.route('', methods=['POST'])
@login_required
def create_review():
    if not current_user.can_create_reviews():
        return jsonify({'success': False, 'message': 'You do not have reviewer privileges'}), 403
    
    form = ReviewForm()
    if form.validate_on_submit():
        # Extract good moments data
        good_moments = request.files.getlist('good_moments')
        # Parse the form data for moments
        # This would need more complex handling for multiple moments with images
        
        review = ReviewService.create_review(
            author_id=current_user.id,
            data=form.data,
            review_poster=form.review_poster.data,
            movie_poster=form.movie_poster.data,
            genres=form.genres.data
        )
        
        if review:
            return jsonify({'success': True, 'message': 'Review created successfully', 'review': review.to_dict()}), 201
        return jsonify({'success': False, 'message': 'Failed to create review'}), 500
    return jsonify({'success': False, 'errors': form.errors}), 400

@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id):
    review = ReviewService.get_review_by_id(review_id)
    if review:
        # Track view
        AnalyticsService.track_review_view(review_id, current_user.id if current_user.is_authenticated else None)
        return jsonify({'success': True, 'review': review.to_dict()}), 200
    return jsonify({'success': False, 'message': 'Review not found'}), 404

@reviews_bp.route('/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    review = ReviewService.get_review_by_id(review_id, increment_view=False)
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404
    
    if review.author_id != current_user.id and not current_user.user_type == 'admin':
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    form = ReviewForm()
    if form.validate_on_submit():
        updated_review, message = ReviewService.update_review(
            review_id=review_id,
            data=form.data,
            review_poster=form.review_poster.data,
            movie_poster=form.movie_poster.data,
            genres=form.genres.data
        )
        if updated_review:
            return jsonify({'success': True, 'message': message, 'review': updated_review.to_dict()}), 200
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    review = ReviewService.get_review_by_id(review_id, increment_view=False)
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404
    
    if review.author_id != current_user.id and not current_user.user_type == 'admin':
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    success, message = ReviewService.delete_review(review_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@reviews_bp.route('/<int:review_id>/like', methods=['POST'])
@login_required
def like_review(review_id):
    success, message = ReviewService.like_review(current_user, review_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@reviews_bp.route('/<int:review_id>/like', methods=['DELETE'])
@login_required
def unlike_review(review_id):
    success, message = ReviewService.unlike_review(current_user, review_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@reviews_bp.route('/<int:review_id>/save', methods=['POST'])
@login_required
def save_review(review_id):
    success, message = ReviewService.save_review(current_user, review_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@reviews_bp.route('/<int:review_id>/save', methods=['DELETE'])
@login_required
def unsave_review(review_id):
    success, message = ReviewService.unsave_review(current_user, review_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@reviews_bp.route('/<int:review_id>/comments', methods=['POST'])
@login_required
def add_comment(review_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment, message = CommentService.create_comment(
            content=form.content.data,
            author_id=current_user.id,
            review_id=review_id,
            parent_comment_id=form.parent_comment_id.data,
            has_emoji=form.has_emoji.data,
            has_gif=form.has_gif.data,
            gif_url=form.gif_url.data
        )
        if comment:
            return jsonify({'success': True, 'message': message, 'comment': comment.to_dict()}), 201
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@reviews_bp.route('/search', methods=['GET'])
def search_reviews():
    query = request.args.get('q', '')
    genre_ids = request.args.getlist('genres')
    min_rating = request.args.get('min_rating')
    max_rating = request.args.get('max_rating')
    has_spoilers = request.args.get('has_spoilers')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', Config.REVIEWS_PER_PAGE, type=int)
    
    if has_spoilers is not None:
        has_spoilers = has_spoilers.lower() == 'true'
    
    pagination = ReviewService.search_reviews(
        query_string=query,
        genre_ids=genre_ids,
        min_rating=min_rating,
        max_rating=max_rating,
        has_spoilers=has_spoilers,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'success': True,
        'reviews': [review.to_dict() for review in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@reviews_bp.route('/feed', methods=['GET'])
@login_required
def get_feed():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', Config.REVIEWS_PER_PAGE, type=int)
    
    pagination = ReviewService.get_feed(current_user, page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'reviews': [review.to_dict() for review in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200