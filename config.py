import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///movie_reviewer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # Pagination
    REVIEWS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 30
    
    # Moderation thresholds
    MAX_REPORTS_SAME_REASON = 4
    MAX_REPORTS_DIFFERENT_REASONS = 7
    
    # File paths for specific uploads
    GOOD_MOMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'good_moments')
    BAD_MOMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'bad_moments')
    REVIEW_POSTERS_FOLDER = os.path.join(UPLOAD_FOLDER, 'review_posters')
    
    # Allowed image formats
    ALLOWED_IMAGE_MIMETYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # In production, ensure SECRET_KEY is set via environment variable

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}