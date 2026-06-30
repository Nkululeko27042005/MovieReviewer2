from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, StringField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Optional, NumberRange

class ReportHandlingForm(FlaskForm):
    action = SelectField('Action', choices=[
        ('dismiss', 'Dismiss Report'),
        ('warning', 'Issue Warning'),
        ('suspend_3days', 'Suspend for 3 Days'),
        ('suspend_7days', 'Suspend for 7 Days'),
        ('suspend_30days', 'Suspend for 30 Days'),
        ('permanent_ban', 'Permanent Ban'),
        ('deactivate', 'Deactivate Account')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional()])
    send_notification = BooleanField('Notify User', default=True)

class UserManagementForm(FlaskForm):
    user_type = SelectField('Change User Type', choices=[
        ('regular', 'Regular User'),
        ('reviewer', 'Reviewer')
    ], validators=[Optional()])
    account_status = SelectField('Account Status', choices=[
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('deactivated', 'Deactivated')
    ], validators=[Optional()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional()])

class SystemSettingsForm(FlaskForm):
    max_reports_same_reason = IntegerField('Max Reports Same Reason', validators=[
        DataRequired(),
        NumberRange(min=1, max=20)
    ])
    max_reports_different_reasons = IntegerField('Max Reports Different Reasons', validators=[
        DataRequired(),
        NumberRange(min=1, max=20)
    ])
    maintenance_mode = BooleanField('Maintenance Mode')