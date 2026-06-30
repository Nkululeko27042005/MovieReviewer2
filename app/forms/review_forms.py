from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, BooleanField, FieldList, FormField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models.genre import Genre

class GoodMomentForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    scene_description = TextAreaField('Scene Description', validators=[Optional(), Length(max=300)])
    images = FileField('Images (multiple allowed)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    order_index = FloatField('Order', default=0)

class BadMomentForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    scene_description = TextAreaField('Scene Description', validators=[Optional(), Length(max=300)])
    images = FileField('Images (multiple allowed)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    order_index = FloatField('Order', default=0)

class ReviewForm(FlaskForm):
    title = StringField('Review Title', validators=[DataRequired(), Length(max=200)])
    movie_name = StringField('Movie Name', validators=[DataRequired(), Length(max=200)])
    overall_rating = FloatField('Overall Rating (0-10)', validators=[
        DataRequired(),
        NumberRange(min=0, max=10)
    ])
    overall_thoughts = TextAreaField('Overall Thoughts/Summary', validators=[DataRequired()])
    
    # Performance ratings
    acting_rating = FloatField('Acting Performance (0-10)', validators=[
        DataRequired(),
        NumberRange(min=0, max=10)
    ])
    cast_selection_rating = FloatField('Cast Selection (0-10)', validators=[
        DataRequired(),
        NumberRange(min=0, max=10)
    ])
    pacing_rating = FloatField('Movie Pacing (0-10)', validators=[
        DataRequired(),
        NumberRange(min=0, max=10)
    ])
    plot_rating = FloatField('Movie Plot/Premise (0-10)', validators=[
        DataRequired(),
        NumberRange(min=0, max=10)
    ])
    
    has_spoilers = BooleanField('Contains Spoilers')
    
    genres = SelectMultipleField('Genres', choices=[])
    review_poster = FileField('Review Poster', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    movie_poster = FileField('Movie Poster', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    
    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.genres.choices = [(str(g.id), g.name) for g in Genre.query.order_by('name')]

class RatingForm(FlaskForm):
    overall_score = FloatField('Overall Score', validators=[DataRequired(), NumberRange(min=0, max=10)])
    story_score = FloatField('Story', validators=[Optional(), NumberRange(min=0, max=10)])
    visuals_score = FloatField('Visuals', validators=[Optional(), NumberRange(min=0, max=10)])
    sound_score = FloatField('Sound', validators=[Optional(), NumberRange(min=0, max=10)])
    rewatchability_score = FloatField('Rewatchability', validators=[Optional(), NumberRange(min=0, max=10)])