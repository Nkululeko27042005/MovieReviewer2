from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SelectField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError
from app.models.user import User

class UserProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    favorite_genres = StringField('Favorite Genres (comma-separated)')
    
    def __init__(self, user_id, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
    
    def validate_username(self, field):
        if field.data:
            user = User.query.filter_by(username=field.data).first()
            if user and user.id != self.user_id:
                raise ValidationError('Username already taken')
    
    def validate_email(self, field):
        if field.data:
            user = User.query.filter_by(email=field.data).first()
            if user and user.id != self.user_id:
                raise ValidationError('Email already registered')

class UserPreferencesForm(FlaskForm):
    favorite_genres = StringField('Favorite Genres (comma-separated)', validators=[Optional()])

class NotificationPreferenceForm(FlaskForm):
    notify_on_follow = BooleanField('Notify when someone follows me')
    notify_on_like = BooleanField('Notify when someone likes my review')
    notify_on_comment = BooleanField('Notify when someone comments on my review')
    notify_on_review_from_followed = BooleanField('Notify when someone I follow posts a review')
    email_notifications = BooleanField('Receive email notifications')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, max=100)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])

class DeleteAccountForm(FlaskForm):
    confirm = StringField('Type "DELETE" to confirm', validators=[DataRequired()])