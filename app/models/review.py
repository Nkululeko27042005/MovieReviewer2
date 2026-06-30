from datetime import datetime
from app import db

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    movie_name = db.Column(db.String(200), nullable=False, index=True)
    
    # Review content
    overall_rating = db.Column(db.Float, nullable=False)  # 0-10 with decimals
    overall_thoughts = db.Column(db.Text, nullable=False)
    
    # Performance ratings (1-10)
    acting_rating = db.Column(db.Float, nullable=False)
    cast_selection_rating = db.Column(db.Float, nullable=False)
    pacing_rating = db.Column(db.Float, nullable=False)
    plot_rating = db.Column(db.Float, nullable=False)
    
    # Spoiler flag
    has_spoilers = db.Column(db.Boolean, default=False)
    
    # Poster
    review_poster_url = db.Column(db.String(500), nullable=True)
    movie_poster_url = db.Column(db.String(500), nullable=True)
    
    # Stats
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    saves_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Status
    is_published = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    good_moments = db.relationship('GoodMoment', backref='review', lazy='dynamic', cascade='all, delete-orphan')
    bad_moments = db.relationship('BadMoment', backref='review', lazy='dynamic', cascade='all, delete-orphan')
    genres = db.relationship('ReviewGenre', backref='review', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='review', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('UserLike', backref='review', lazy='dynamic')
    saves = db.relationship('UserSave', backref='review', lazy='dynamic')
    
    def calculate_average_rating(self):
        """Calculate average of all performance ratings"""
        ratings = [self.acting_rating, self.cast_selection_rating, self.pacing_rating, self.plot_rating]
        return sum(ratings) / len(ratings)
    
    def to_dict(self, include_moments=True):
        data = {
            'id': self.id,
            'title': self.title,
            'movie_name': self.movie_name,
            'overall_rating': self.overall_rating,
            'overall_thoughts': self.overall_thoughts,
            'acting_rating': self.acting_rating,
            'cast_selection_rating': self.cast_selection_rating,
            'pacing_rating': self.pacing_rating,
            'plot_rating': self.plot_rating,
            'average_performance_rating': self.calculate_average_rating(),
            'has_spoilers': self.has_spoilers,
            'review_poster_url': self.review_poster_url,
            'movie_poster_url': self.movie_poster_url,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'saves_count': self.saves_count,
            'views_count': self.views_count,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'author_id': self.author_id,
            'author_username': self.author.username if self.author else None,
            'genres': [rg.genre.name for rg in self.genres]
        }
        
        if include_moments:
            data['good_moments'] = [moment.to_dict() for moment in self.good_moments]
            data['bad_moments'] = [moment.to_dict() for moment in self.bad_moments]
        
        return data
    
    def __repr__(self):
        return f'<Review {self.movie_name} by User {self.author_id}>'

class GoodMoment(db.Model):
    __tablename__ = 'good_moments'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_urls = db.Column(db.JSON, default=list)  # List of image URLs (can be multiple per moment)
    scene_description = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'image_urls': self.image_urls or [],
            'scene_description': self.scene_description,
            'order_index': self.order_index
        }

class BadMoment(db.Model):
    __tablename__ = 'bad_moments'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_urls = db.Column(db.JSON, default=list)  # List of image URLs (can be multiple per moment)
    scene_description = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'image_urls': self.image_urls or [],
            'scene_description': self.scene_description,
            'order_index': self.order_index
        }

class ReviewGenre(db.Model):
    __tablename__ = 'review_genres'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('review_id', 'genre_id', name='unique_review_genre'),)

class ReviewRating(db.Model):
    """Stores individual rating components for a review"""
    __tablename__ = 'review_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False, unique=True)
    overall_score = db.Column(db.Float, nullable=False)
    story_score = db.Column(db.Float, nullable=True)
    visuals_score = db.Column(db.Float, nullable=True)
    sound_score = db.Column(db.Float, nullable=True)
    rewatchability_score = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        return {
            'overall_score': self.overall_score,
            'story_score': self.story_score,
            'visuals_score': self.visuals_score,
            'sound_score': self.sound_score,
            'rewatchability_score': self.rewatchability_score
        }