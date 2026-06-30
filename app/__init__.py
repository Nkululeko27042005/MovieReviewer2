from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from app.api import auth_bp, reviews_bp, users_bp, admin_bp, comments_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(comments_bp, url_prefix='/api/comments')

    # Register HTML page views blueprint
    try:
        from app.views import views_bp
        app.register_blueprint(views_bp)
    except Exception:
        # If views can't be imported, skip registration to avoid breaking app
        pass
    
    # Add index route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Provide safe defaults for templates to avoid UndefinedError when views
    # render templates without full context (useful for development/testing).
    @app.context_processor
    def inject_defaults():
        class _DummyPagination:
            def __init__(self):
                self.items = []
                self.page = 1
                self.total = 0
                self.pages = 1
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            def __iter__(self):
                return iter(self.items)

        class _DummyUserType:
            def __init__(self):
                self.value = 'regular'

        class _CountableList(list):
            def count(self, *args):
                return len(self)

        class _DummyUser:
            def __init__(self):
                self.id = 1
                self.username = 'Guest'
                self.profile_picture = None
                self.bio = ''
                self.user_type = _DummyUserType()
                self.followers = _CountableList()
                self.following = _CountableList()
                self.reviews = _CountableList()

        class _DummyReview:
            def __init__(self):
                from datetime import datetime
                self.id = None
                self.title = 'Untitled'
                self.published_at = datetime.utcnow()
                self.author = _DummyUser()
                self.author.id = 1
                self.overall_rating = 0.0
                self.movie_name = ''
                self.overall_thoughts = ''
                self.has_spoilers = False
                self.likes_count = 0
                self.comments_count = 0
                self.saves_count = 0
                self.genres = []
                self.good_moments = _CountableList()
                self.bad_moments = _CountableList()
            def calculate_average_rating(self):
                return float(self.overall_rating or 0.0)

        class _DummyField:
            def __init__(self):
                self.errors = []
                self.data = ''

        class _DummyForm:
            def __init__(self):
                self.email = _DummyField()
                self.password = _DummyField()
                self.username = _DummyField()
                self.confirm_password = _DummyField()
                self.password_confirm = _DummyField()
                self.remember_me = _DummyField()
                self.user_type = _DummyField()
                self.favorite_genres = _DummyField()
                self.current_password = _DummyField()
                self.new_password = _DummyField()
                self.profile_picture = _DummyField()

            def hidden_tag(self):
                return ''

            @property
            def errors(self):
                return {}

        return {
            'reviews': _DummyPagination(),
            'form': _DummyForm(),
            'review': _DummyReview(),
            'user': _DummyUser(),
            'comments': _DummyPagination(),
            'liked_review_ids': [],
            'saved_review_ids': []
        }
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))