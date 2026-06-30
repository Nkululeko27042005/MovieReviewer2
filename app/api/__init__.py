from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
reviews_bp = Blueprint('reviews', __name__)
users_bp = Blueprint('users', __name__)
admin_bp = Blueprint('admin', __name__)
comments_bp = Blueprint('comments', __name__)

# Import route files at the END to avoid circular imports
# This is done after blueprints are created
def _register_routes():
    """Register all route modules - called after blueprints are created."""
    from . import auth_routes
    from . import review_routes
    from . import user_routes
    from . import admin_routes
    from . import comment_routes

_register_routes()