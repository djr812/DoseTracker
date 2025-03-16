from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField('Username (Email Address)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class SignUpForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])


class MedicineForm(FlaskForm):
    name = StringField('Medicine Name', validators=[DataRequired()])
    dosage = StringField('Dosage', validators=[DataRequired()])
    frequency = StringField('Frequency', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])


class ReminderForm(FlaskForm):
    reminder_time = DateTimeLocalField('Reminder Time', validators=[Optional()])
    reminder_message = TextAreaField('Reminder Message', validators=[Optional()])
    status = SelectField('Reminder Status', choices=[('pending', 'Pending'), ('sent', 'Sent')], default='pending', validators=[DataRequired()])