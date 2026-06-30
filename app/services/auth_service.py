from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import generate_password_hash, check_password_hash
from app.models.user import User, UserType, AccountStatus, UserFavoriteGenre
from app.models.genre import Genre
from app import db
from datetime import datetime

class AuthService:
    
    @staticmethod
    def register_user(username, email, password, user_type, favorite_genres=None):
        """Register a new user"""
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return None, 'Email already registered'
        if User.query.filter_by(username=username).first():
            return None, 'Username already taken'
        
        # Hash password
        password_hash = generate_password_hash(password).decode('utf-8')
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        user.user_type = UserType.REVIEWER if user_type == 'reviewer' else UserType.REGULAR
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Add favorite genres if provided
        if favorite_genres:
            genre_names = [g.strip() for g in favorite_genres.split(',') if g.strip()]
            saved_genre_names = []
            for genre_name in genre_names:
                genre = Genre.query.filter_by(name=genre_name).first()
                if genre:
                    fav = UserFavoriteGenre(user_id=user.id, genre_id=genre.id)
                    db.session.add(fav)
                    saved_genre_names.append(genre.name)
            user.favorite_genres = ", ".join(saved_genre_names)
        
        db.session.commit()
        return user, 'Registration successful'
    
    @staticmethod
    def login_user(email, password, remember=False):
        """Authenticate and login user"""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return None, 'User not found'
        
        if user.account_status != AccountStatus.ACTIVE:
            return None, f'Account is {user.account_status.value}. Please contact support.'
        
        if check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user, 'Login successful'
        
        return None, 'Invalid password'
    
    @staticmethod
    def logout_user():
        """Logout current user"""
        logout_user()
        return True, 'Logged out successfully'
    
    @staticmethod
    def get_current_user():
        """Get currently logged in user"""
        return current_user if current_user.is_authenticated else None
    
    @staticmethod
    def change_user_type(user, new_type):
        """Change user account type"""
        if user.user_type == UserType.ADMIN:
            return False, 'Cannot change admin account type'
        
        if new_type == 'reviewer':
            user.user_type = UserType.REVIEWER
        elif new_type == 'regular':
            user.user_type = UserType.REGULAR
        else:
            return False, 'Invalid user type'
        
        db.session.commit()
        return True, f'Account type changed to {new_type}'