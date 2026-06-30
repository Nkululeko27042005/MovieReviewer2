from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField, StringField
from wtforms.validators import DataRequired, Length, Optional, URL

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=1000)])
    has_emoji = BooleanField('Contains Emoji')
    has_gif = BooleanField('Contains GIF')
    gif_url = StringField('GIF URL', validators=[Optional(), URL()])
    parent_comment_id = StringField('Parent Comment ID', validators=[Optional()])