from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms.auth_forms import LoginForm, RegistrationForm
from app.forms.review_forms import ReviewForm
from app.forms.comment_forms import CommentForm
from app.forms.user_forms import UserProfileForm, ChangePasswordForm, DeleteAccountForm
from app.services.review_service import ReviewService
from app.services.comment_service import CommentService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService
from app.models.user import UserType, User
from app.models.review import Review
from app import db
from sqlalchemy import or_
import re

views_bp = Blueprint('views', __name__)

def _parse_moments(type_prefix):
    """Parse dynamic moments (good or bad) from HTML form & files."""
    moments_dict = {}
    
    # 1. Parse text fields
    pattern = re.compile(rf'^{type_prefix}_moments\[(\d+)\]\[(\w+)\]$')
    for key, value in request.form.items():
        match = pattern.match(key)
        if match:
            idx = int(match.group(1))
            field = match.group(2)
            if idx not in moments_dict:
                moments_dict[idx] = {}
            moments_dict[idx][field] = value
            
    # 2. Parse files
    file_pattern = re.compile(rf'^{type_prefix}_moments\[(\d+)\]\[images\]$')
    for key in request.files:
        match = file_pattern.match(key)
        if match:
            idx = int(match.group(1))
            files = request.files.getlist(key)
            if idx not in moments_dict:
                moments_dict[idx] = {}
            valid_files = [f for f in files if f.filename]
            if valid_files:
                moments_dict[idx]['images'] = valid_files
                
    sorted_indices = sorted(moments_dict.keys())
    return [moments_dict[idx] for idx in sorted_indices]

# Admin requirement decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type.value != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('views.feed_page'))
        return f(*args, **kwargs)
    return decorated_function

@views_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('views.feed_page'))
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user, message = AuthService.login_user(
                email=form.email.data,
                password=form.password.data,
                remember=form.remember_me.data
            )
            if user:
                next_page = request.args.get('next')
                return redirect(next_page or url_for('views.feed_page'))
            flash(message, 'error')
        else:
            flash('Please correct the form errors.', 'error')
    return render_template('auth/login.html', form=form)

@views_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('views.feed_page'))
    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user, message = AuthService.register_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                user_type=form.user_type.data,
                favorite_genres=form.favorite_genres.data
            )
            if user:
                AuthService.login_user(email=form.email.data, password=form.password.data)
                flash('Account created successfully!', 'success')
                return redirect(url_for('views.feed_page'))
            flash(message, 'error')
        else:
            flash('Please correct the form errors.', 'error')
    return render_template('auth/register.html', form=form)

@views_bp.route('/logout')
@login_required
def logout_page():
    AuthService.logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('views.login_page'))

@views_bp.route('/feed')
@login_required
def feed_page():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'newest')
    
    if search_query:
        pagination = ReviewService.search_reviews(query_string=search_query, page=page, per_page=per_page)
    else:
        pagination = ReviewService.get_feed(current_user, page=page, per_page=per_page, sort_by=sort_by)
        
    return render_template('reviews/feed.html', reviews=pagination, current_sort=sort_by)

@views_bp.route('/reviews/<int:review_id>')
def review_detail_page(review_id):
    review = ReviewService.get_review_by_id(review_id)
    if not review:
        flash('Review not found.', 'error')
        return redirect(url_for('views.feed_page'))
    comments = CommentService.get_comments_for_review(review_id) if hasattr(CommentService, 'get_comments_for_review') else []
    comment_form = CommentForm()
    
    is_liked = False
    is_saved = False
    if current_user.is_authenticated:
        from app.models.user import UserLike, UserSave
        is_liked = UserLike.query.filter_by(user_id=current_user.id, review_id=review_id).first() is not None
        is_saved = UserSave.query.filter_by(user_id=current_user.id, review_id=review_id).first() is not None
        
    return render_template('reviews/detail.html', review=review, comments=comments, comment_form=comment_form, is_liked=is_liked, is_saved=is_saved)

@views_bp.route('/reviews/<int:review_id>/comments', methods=['POST'])
@login_required
def add_comment_page(review_id):
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
            flash('Comment added successfully.', 'success')
        else:
            flash(message, 'error')
    else:
        flash('Please correct comment form errors.', 'error')
    return redirect(url_for('views.review_detail_page', review_id=review_id))

@views_bp.route('/create-review', methods=['GET', 'POST'])
@login_required
def create_review_page():
    if not current_user.can_create_reviews():
        flash('You do not have reviewer privileges.', 'error')
        return redirect(url_for('views.feed_page'))
    
    form = ReviewForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            good_moments = _parse_moments('good')
            bad_moments = _parse_moments('bad')
            
            review = ReviewService.create_review(
                author_id=current_user.id,
                data=form.data,
                good_moments_data=good_moments,
                bad_moments_data=bad_moments,
                review_poster=form.review_poster.data,
                movie_poster=form.movie_poster.data,
                genres=form.genres.data
            )
            if review:
                flash('Review published successfully!', 'success')
                return redirect(url_for('views.review_detail_page', review_id=review.id))
            flash('Failed to create review.', 'error')
        else:
            flash('Please correct form errors.', 'error')
            
    return render_template('reviews/create.html', form=form)

@views_bp.route('/reviews/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review_page(review_id):
    review = ReviewService.get_review_by_id(review_id, increment_view=False)
    if not review:
        flash('Review not found.', 'error')
        return redirect(url_for('views.feed_page'))
        
    if review.author_id != current_user.id and current_user.user_type.value != 'admin':
        flash('Permission denied.', 'error')
        return redirect(url_for('views.review_detail_page', review_id=review_id))
        
    form = ReviewForm(obj=review)
    review_genre_ids = [str(rg.genre_id) for rg in review.genres]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            good_moments = _parse_moments('good')
            bad_moments = _parse_moments('bad')
            
            updated_review, message = ReviewService.update_review(
                review_id=review_id,
                data=form.data,
                good_moments_data=good_moments,
                bad_moments_data=bad_moments,
                review_poster=form.review_poster.data,
                movie_poster=form.movie_poster.data,
                genres=form.genres.data
            )
            if updated_review:
                flash(message, 'success')
                return redirect(url_for('views.review_detail_page', review_id=review_id))
            flash(message, 'error')
        else:
            flash('Please correct form errors.', 'error')
            
    return render_template('reviews/edit.html', form=form, review=review, review_genre_ids=review_genre_ids)

@views_bp.route('/users/<int:user_id>')
def profile_page(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('views.feed_page'))
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort', 'newest')
    reviews = ReviewService.get_reviews_by_user(user_id, page=page, per_page=per_page, sort_by=sort_by)
    
    if current_user.is_authenticated and current_user.id != user_id:
        AnalyticsService.update_user_daily_stats(user_id, 'profile_view')
        
    analytics = None
    if current_user.is_authenticated and user_id == current_user.id:
        try:
            analytics = AnalyticsService.get_user_analytics_summary(user_id)
        except Exception:
            analytics = None
            
    is_following = False
    if current_user.is_authenticated and current_user.id != user_id:
        is_following = current_user.is_following(user)
        
    return render_template('users/profile.html', user=user, reviews=reviews, analytics=analytics, sort_by=sort_by, is_following=is_following)

@views_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile_page():
    form = UserProfileForm(user_id=current_user.id, obj=current_user)
    if request.method == 'POST':
        if form.validate_on_submit():
            success, message = UserService.update_profile(
                user=current_user,
                data=form.data,
                profile_picture=form.profile_picture.data
            )
            if success:
                flash(message, 'success')
                return redirect(url_for('views.profile_page', user_id=current_user.id))
            flash(message, 'error')
        else:
            flash('Please correct form errors.', 'error')
            
    return render_template('users/edit_profile.html', form=form)

@views_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password_page():
    form = ChangePasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            success, message = UserService.change_password(
                user=current_user,
                current_password=form.current_password.data,
                new_password=form.new_password.data
            )
            if success:
                flash(message, 'success')
                return redirect(url_for('views.edit_profile_page'))
            flash(message, 'error')
        else:
            flash('Please correct form errors.', 'error')
            
    return render_template('users/change_password.html', form=form)

@views_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account_page():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if form.confirm.data != 'DELETE':
            flash('Please type DELETE to confirm.', 'error')
            return redirect(url_for('views.edit_profile_page'))
        success, message = UserService.delete_user_account(current_user)
        if success:
            AuthService.logout_user()
            flash('Your account has been deleted.', 'success')
            return redirect(url_for('views.login_page'))
        flash(message, 'error')
    else:
        flash('Form verification failed.', 'error')
    return redirect(url_for('views.edit_profile_page'))

@views_bp.route('/users/<int:user_id>/followers')
def followers_page(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('views.feed_page'))
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    followers = UserService.get_followers(user_id, page=page, per_page=per_page)
    
    return render_template('users/followers.html', user_id=user_id, followers=followers)

@views_bp.route('/users/<int:user_id>/following')
def following_page(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('views.feed_page'))
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    following = UserService.get_following(user_id, page=page, per_page=per_page)
    
    return render_template('users/following.html', user_id=user_id, following=following)

@views_bp.route('/saved-reviews')
@login_required
def saved_reviews_page():
    page = request.args.get('page', 1, type=int)
    from config import Config
    per_page = request.args.get('per_page', Config.REVIEWS_PER_PAGE, type=int)
    reviews = UserService.get_saved_reviews(current_user, page=page, per_page=per_page)
    
    return render_template('users/saved_reviews.html', reviews=reviews)

@views_bp.route('/notifications')
@login_required
def notifications_page():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    
    notifications = NotificationService.get_user_notifications(
        current_user.id,
        limit=limit,
        offset=offset
    )
    
    unread_count = NotificationService.get_unread_count(current_user.id)
    if unread_count > 0:
        NotificationService.mark_all_as_read(current_user.id)
        unread_count = 0
        
    class SimplePagination:
        def __init__(self, page, limit, total):
            self.page = page
            self.limit = limit
            self.total = total
            self.pages = (total + limit - 1) // limit
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1
            
    total_notifications = current_user.notifications.count()
    pagination = SimplePagination(page, limit, total_notifications)
    
    return render_template('notfications/index.html', notifications=notifications, pagination=pagination, unread_count=unread_count)

# Admin Pages
@views_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard_page():
    stats = AdminService.get_platform_stats()
    from app.models.report import Report
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_reports=recent_reports)

@views_bp.route('/admin/reports')
@login_required
@admin_required
def admin_reports_page():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    reports = AdminService.get_all_reports(page=page, per_page=per_page, status=status)
    return render_template('admin/reports.html', reports=reports, status=status)

@views_bp.route('/admin/users')
@login_required
@admin_required
def admin_users_page():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_query = request.args.get('search')
    
    query = User.query
    if search_query:
        query = query.filter(or_(User.username.like(f'%{search_query}%'), User.email.like(f'%{search_query}%')))
        
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=pagination, search=search_query)

@views_bp.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics_page():
    date_str = request.args.get('date')
    if date_str:
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            from datetime import date
            date_obj = date.today()
            date_str = date_obj.strftime('%Y-%m-%d')
    else:
        from datetime import date
        date_obj = date.today()
        date_str = date_obj.strftime('%Y-%m-%d')
        
    analytics = AnalyticsService.get_global_daily_analytics(date_obj)
    return render_template('admin/analytics.html', analytics=analytics, date=date_str)

