from flask import request, jsonify, session
from flask_login import login_required, current_user, logout_user
from app.api import auth_bp
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.notification_service import NotificationService
from app.forms.auth_forms import RegistrationForm, LoginForm
from app import db

@auth_bp.route('/register', methods=['POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user, message = AuthService.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            user_type=form.user_type.data,
            favorite_genres=form.favorite_genres.data
        )
        if user:
            return jsonify({'success': True, 'message': message, 'user': user.to_dict()}), 201
        return jsonify({'success': False, 'message': message}), 400
    return jsonify({'success': False, 'errors': form.errors}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user, message = AuthService.login_user(
            email=form.email.data,
            password=form.password.data,
            remember=form.remember_me.data
        )
        if user:
            return jsonify({'success': True, 'message': message, 'user': user.to_dict()}), 200
        return jsonify({'success': False, 'message': message}), 401
    return jsonify({'success': False, 'errors': form.errors}), 400

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    AuthService.logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    user = AuthService.get_current_user()
    if user:
        return jsonify({'success': True, 'user': user.to_dict()}), 200
    return jsonify({'success': False, 'message': 'Not authenticated'}), 401

@auth_bp.route('/change-user-type', methods=['PUT'])
@login_required
def change_user_type():
    data = request.get_json()
    new_type = data.get('user_type')
    
    if not new_type:
        return jsonify({'success': False, 'message': 'User type required'}), 400
    
    success, message = AuthService.change_user_type(current_user, new_type)
    if success:
        return jsonify({'success': True, 'message': message, 'user': current_user.to_dict()}), 200
    return jsonify({'success': False, 'message': message}), 400