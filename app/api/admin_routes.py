from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import admin_bp
from app.services.admin_service import AdminService
from app.services.user_service import UserService
from app.services.analytics_service import AnalyticsService
from app.models.user import UserType
from app.forms.admin_forms import ReportHandlingForm, UserManagementForm
from config import Config

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != UserType.ADMIN:
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/reports/pending', methods=['GET'])
@login_required
@admin_required
def get_pending_reports():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = AdminService.get_pending_reports(page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'reports': [report.to_dict() for report in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@admin_bp.route('/reports', methods=['GET'])
@login_required
@admin_required
def get_all_reports():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    pagination = AdminService.get_all_reports(page=page, per_page=per_page, status=status)
    return jsonify({
        'success': True,
        'reports': [report.to_dict() for report in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200

@admin_bp.route('/reports/<int:report_id>/handle', methods=['PUT'])
@login_required
@admin_required
def handle_report(report_id):
    form = ReportHandlingForm()
    if form.validate_on_submit():
        success, message = AdminService.handle_report(
            report_id=report_id,
            admin_id=current_user.id,
            action=form.action.data,
            notes=form.admin_notes.data
        )
        if success:
            return jsonify({'success': True, 'message': message}), 200
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@admin_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_report(report_id):
    success, message = AdminService.delete_report(report_id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@admin_bp.route('/users/<int:user_id>/manage', methods=['PUT'])
@login_required
@admin_required
def manage_user(user_id):
    form = UserManagementForm()
    if form.validate_on_submit():
        # Handle user management actions
        if form.user_type.data:
            success, message = AdminService.manage_user(
                user_id=user_id,
                action=f"make_{form.user_type.data}",
                notes=form.admin_notes.data
            )
            if not success:
                return jsonify({'success': False, 'message': message}), 400
        
        if form.account_status.data:
            success, message = AdminService.manage_user(
                user_id=user_id,
                action=form.account_status.data,
                notes=form.admin_notes.data
            )
            if not success:
                return jsonify({'success': False, 'message': message}), 400
        
        return jsonify({'success': True, 'message': 'User updated successfully'}), 200
    return jsonify({'success': False, 'errors': form.errors}), 400

@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_platform_stats():
    stats = AdminService.get_platform_stats()
    return jsonify({'success': True, 'stats': stats}), 200

@admin_bp.route('/analytics/daily', methods=['GET'])
@login_required
@admin_required
def get_daily_analytics():
    date_str = request.args.get('date')
    if date_str:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        from datetime import date
        date_obj = date.today()
    
    analytics = AnalyticsService.get_global_daily_analytics(date_obj)
    if analytics:
        return jsonify({'success': True, 'analytics': analytics}), 200
    return jsonify({'success': True, 'analytics': None, 'message': 'No data for this date'}), 200

@admin_bp.route('/analytics/calculate-daily', methods=['POST'])
@login_required
@admin_required
def calculate_daily_analytics():
    date_str = request.get_json().get('date')
    if date_str:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        from datetime import date
        date_obj = date.today()
    
    analytics = AnalyticsService.calculate_global_daily_analytics(date_obj)
    return jsonify({
        'success': True,
        'message': f'Analytics calculated for {date_obj}',
        'analytics': analytics.to_dict() if analytics else None
    }), 200

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    from app.models.user import User
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in pagination.items],
        'page': pagination.page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }), 200