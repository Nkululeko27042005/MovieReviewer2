from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=100)
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    user_type = SelectField('Account Type', choices=[
        ('regular', 'Regular User (Browse, Like, Comment)'),
        ('reviewer', 'Reviewer (Create and Manage Reviews)')
    ], validators=[DataRequired()])
    
    favorite_genres = StringField('Favorite Genres (comma-separated)')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class AccountTypeForm(FlaskForm):
    user_type = SelectField('Change Account Type', choices=[
        ('regular', 'Regular User'),
        ('reviewer', 'Reviewer')
    ], validators=[DataRequired()])