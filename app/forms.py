from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, InputRequired, Length
from wtforms.fields import FieldList


class LoginForm(FlaskForm):
    email = StringField('Username (Email Address)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class SignUpForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    phone_number = StringField('Phone Number', validators=[InputRequired(), Length(min=10, max=15)])


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])


class MedicineForm(FlaskForm):
    name = StringField('Medicine Name', validators=[DataRequired()])
    dosage = StringField('Dosage', validators=[DataRequired()])
    
    # Change to a SelectField for Frequency
    frequency = SelectField(
        'Frequency',
        choices=[
            ('Once a Day', 'Once a Day'),
            ('Twice a Day', 'Twice a Day'),
            ('Three Times a Day', 'Three Times a Day'),
            ('Four Times a Day', 'Four Times a Day')
        ],
        validators=[DataRequired()]
    )
    
    notes = TextAreaField('Notes', validators=[Optional()])


class ReminderForm(FlaskForm):
    reminder_time = TimeField('Reminder Time', validators=[Optional()], format='%H:%M') 
    reminder_message = TextAreaField('Reminder Message', validators=[Optional()])
    status = SelectField('Reminder Status', choices=[('pending', 'Pending'), ('sent', 'Sent')], default='pending', validators=[DataRequired()])


class EditMedicineForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    dosage = StringField('Dose', validators=[DataRequired()])

    frequency = SelectField(
        'Frequency',
        choices=[('Once a Day', 'Once a Day'),
                 ('Twice a Day', 'Twice a Day'),
                 ('Three Times a Day', 'Three Times a Day'),
                 ('Four Times a Day', 'Four Times a Day')],
        validators=[InputRequired()]
    )

    notes = TextAreaField('Notes', validators=[Optional()])

    reminder_time = FieldList(TimeField('Reminder Time', format='%H:%M'), min_entries=1, max_entries=4)
    reminder_message = FieldList(StringField('Reminder Message'), min_entries=1, max_entries=4)
    
    # Remove the FieldList for status (we'll handle it manually in the route)



