from flask import jsonify
from flask_login import login_required, current_user
from app.api import comments_bp
from app.services.comment_service import CommentService

@comments_bp.route('/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    success, message = CommentService.like_comment(comment_id, current_user.id)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    is_admin = current_user.user_type.value == 'admin'
    success, message = CommentService.delete_comment(comment_id, current_user.id, is_admin)
    if success:
        return jsonify({'success': True, 'message': message}), 200
    return jsonify({'success': False, 'message': message}), 400
