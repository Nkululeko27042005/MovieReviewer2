from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import users_bp
from app.services.user_service import UserService
from app.services.review_service import ReviewService
from app.services.notification_service import NotificationService
from app.services.analytics_service import AnalyticsService
from app.forms.user_forms import UserProfileForm, ChangePasswordForm, DeleteAccountForm
from app.forms.auth_forms import AccountTypeForm
from config import Config

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Track profile view (if authenticated and not viewing own profile)
    if current_user.is_authenticated and current_user.id != user_id:
        AnalyticsService.update_user_daily_stats(user_id, 'profile_view')
    
    return jsonify({'success': True, 'user': user.to_dict()}), 200

@users_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    form = UserProfileForm(current_user.id)
    if form.validate_on_submit():
        success, message = UserService.update_profile(
            user=current_user,
            data=form.data,
            profile_picture=form.profile_picture.data
        )
        if success:
            return jsonify({'success': True, 'message': message, 'user': current_user.to_dict()}), 200
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@users_bp.route('/change-password', methods=['PUT'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        success, message = UserService.change_password(
            user=current_user,
            current_password=form.current_password.data,
            new_password=form.new_password.data
        )
        if success:
            return jsonify({'success': True, 'message': message}), 200
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@users_bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if form.confirm.data != 'DELETE':
            return jsonify({'success': False, 'message': 'Please type DELETE to confirm'}), 400
        
        success, message = UserService.delete_user_account(current_user)
        if success:
            return jsonify({'success': True, 'message': message}), 200
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@users_bp.route('/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot follow yourself'}), 400
    
    success, message = UserService.follow_user(current_user, user_id)
    if success:
        followee = UserService.get_user_by_id(user_id)
        if followee:
            NotificationService.notify_follow(followee, current_user)
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@users_bp.route('/<int:user_id>/unfollow', methods=['DELETE'])
@login_required
def unfollow_user(user_id):
    success, message = UserService.unfollow_user(current_user, user_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@users_bp.route('/<int:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', Config.REVIEWS_PER_PAGE, type=int)
    sort_by = request.args.get('sort_by', 'newest')
    
    pagination = ReviewService.get_reviews_by_user(user_id, page=page, per_page=per_page, sort_by=sort_by)
    return jsonify({
        'success': True,
        'reviews': [review.to_dict() for review in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@users_bp.route('/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = UserService.get_followers(user_id, page=page, per_page=per_page)
    if pagination is None:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@users_bp.route('/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = UserService.get_following(user_id, page=page, per_page=per_page)
    if pagination is None:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@users_bp.route('/saved-reviews', methods=['GET'])
@login_required
def get_saved_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', Config.REVIEWS_PER_PAGE, type=int)
    
    pagination = UserService.get_saved_reviews(current_user, page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'reviews': [review.to_dict() for review in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@users_bp.route('/analytics', methods=['GET'])
@login_required
def get_user_analytics():
    days = request.args.get('days', 30, type=int)
    
    # Get user stats
    stats = UserService.get_user_stats(current_user.id)
    
    # Get detailed analytics
    analytics = AnalyticsService.get_user_analytics_summary(current_user.id, days=days)
    
    return jsonify({
        'success': True,
        'stats': stats,
        'analytics': analytics
    }), 200

@users_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    notifications = NotificationService.get_user_notifications(
        current_user.id, 
        status=status, 
        limit=limit, 
        offset=offset
    )
    
    unread_count = NotificationService.get_unread_count(current_user.id)
    
    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count,
        'total': current_user.notifications.count()
    }), 200

@users_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    count = NotificationService.mark_all_as_read(current_user.id)
    return jsonify({
        'success': True,
        'message': f'Marked {count} notifications as read'
    }), 200