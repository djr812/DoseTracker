"""
forms.py
--------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/forms.py

Purpose:    Contains Flask-WTF form classes for handling user input and form validation, including login, 
            registration, medicine management, and reminder forms.
"""


from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SelectField,
    TimeField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Optional,
    InputRequired,
    Length,
)
from wtforms.fields import FieldList


class LoginForm(FlaskForm):
    """
    Login form for user authentication.

    Fields:
        email (str): The user's email address, used as the username for login.
        password (str): The user's password, used for authentication.

    Validators:
        DataRequired: Ensures that the field is not left empty.
        Email: Validates that the input is a proper email format.

    """

    email = StringField(
        "Username (Email Address)", validators=[DataRequired(), Email()]
    )
    password = PasswordField("Password", validators=[DataRequired()])


class SignUpForm(FlaskForm):
    """
    Sign Up form for user registration.

    Fields:
        email (str): The user's email address, used for registration and as a unique identifier.
        password (str): The user's password, used for account security.
        confirm_password (str): A field to confirm that the user’s password is correct.
        phone_number (str): The user's phone number, with length constraints to ensure proper formatting.

    Validators:
        DataRequired: Ensures that the field is not left empty.
        Email: Ensures that the email is in a valid email format.
        EqualTo: Ensures the confirm_password field matches the password.
        Length: Ensures the phone number is between 10 and 15 characters.
        InputRequired: Ensures the phone number field is provided.

    """

    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    phone_number = StringField(
        "Phone Number", validators=[InputRequired(), Length(min=10, max=15)]
    )


class ForgotPasswordForm(FlaskForm):
    """
    Forgot Password form for user password recovery.

    Fields:
        email (str): The user's email address, which is used to identify the account for password recovery.

    Validators:
        DataRequired: Ensures that the field is not left empty.
        Email: Ensures that the input is in a valid email format.

    """

    email = StringField("Email Address", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    """
    Reset Password form for updating the user's password.

    Fields:
        password (str): The new password chosen by the user.
        confirm_password (str): A confirmation field to ensure the new password is entered correctly.

    Validators:
        DataRequired: Ensures that the field is not left empty.
        EqualTo: Ensures that the confirm_password field matches the password field.

    """

    password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )


class MedicineForm(FlaskForm):
    """
    Medicine form for adding or editing medicine information.

    Fields:
        name (str): The name of the medicine.
        dosage (str): The dosage of the medicine.
        frequency (str): The frequency at which the medicine should be taken, chosen from predefined options.
        notes (str): Optional additional notes related to the medicine.

    Validators:
        DataRequired: Ensures that the field is not left empty.
        Optional: Allows the field to be left empty (for optional fields).
        SelectField choices: Ensures that the user selects from the predefined options for the frequency.

    """

    name = StringField("Medicine Name", validators=[DataRequired()])
    dosage = StringField("Dosage", validators=[DataRequired()])

    frequency = SelectField(
        "Frequency",
        choices=[
            ("Once a Day", "Once a Day"),
            ("Twice a Day", "Twice a Day"),
            ("Three Times a Day", "Three Times a Day"),
            ("Four Times a Day", "Four Times a Day"),
        ],
        validators=[DataRequired()],
    )

    notes = TextAreaField("Notes", validators=[Optional()])


class ReminderForm(FlaskForm):
    """
    Reminder form for creating or editing medication reminders.

    Fields:
        reminder_time (str): The time at which the reminder should be triggered, in the format HH:MM.
        reminder_message (str): An optional message that will be sent with the reminder.
        status (str): The status of the reminder, which can either be 'pending' or 'sent'.

    Validators:
        DataRequired: Ensures that the field is not left empty (used for the status field).
        Optional: Allows the field to be left empty (used for the reminder time and reminder message fields).
        SelectField choices: Ensures the user selects from the predefined options for the reminder status.

    """

    reminder_time = TimeField("Reminder Time", validators=[Optional()], format="%H:%M")
    reminder_message = TextAreaField("Reminder Message", validators=[Optional()])
    status = SelectField(
        "Reminder Status",
        choices=[("pending", "Pending"), ("sent", "Sent")],
        default="pending",
        validators=[DataRequired()],
    )


class EditMedicineForm(FlaskForm):
    """
    Edit Medicine form for updating or modifying medicine details.

    Fields:
        name (str): The name of the medicine.
        dosage (str): The dosage of the medicine.
        frequency (str): The frequency at which the medicine should be taken, selected from predefined options.
        notes (str): Optional additional notes related to the medicine.
        reminder_time (list of str): A list of times at which the user wants to be reminded to take the medicine.
        reminder_message (list of str): A list of custom messages for each reminder time.

    Validators:
        DataRequired: Ensures that the field is not left empty (used for name, dosage, and frequency fields).
        InputRequired: Ensures that at least one reminder time is provided (used for reminder_time and reminder_message).
        Optional: Allows the field to be left empty (used for notes).
        SelectField choices: Ensures that the user selects from predefined options for the frequency.

    """

    name = StringField("Name", validators=[DataRequired()])
    dosage = StringField("Dose", validators=[DataRequired()])

    frequency = SelectField(
        "Frequency",
        choices=[
            ("Once a Day", "Once a Day"),
            ("Twice a Day", "Twice a Day"),
            ("Three Times a Day", "Three Times a Day"),
            ("Four Times a Day", "Four Times a Day"),
        ],
        validators=[InputRequired()],
    )

    notes = TextAreaField("Notes", validators=[Optional()])

    reminder_time = FieldList(
        TimeField("Reminder Time", format="%H:%M"), min_entries=1, max_entries=4
    )
    reminder_message = FieldList(
        StringField("Reminder Message"), min_entries=1, max_entries=4
    )


class UserAdminForm(FlaskForm):
    """
    User Admin form for managing user profile and notification preferences.

    Fields:
        phone_number (str): The phone number associated with the user profile. Limited to a maximum of 15 characters.
        receive_sms_reminders (bool): A boolean indicating whether the user should receive SMS reminders for their medication. Defaults to True.

    Validators:
        Length: Ensures that the phone number does not exceed 15 characters.
        BooleanField default: Sets the default value for the `receive_sms_reminders` field to `True`.

    """

    phone_number = StringField("Phone Number", validators=[Length(max=15)])
    receive_sms_reminders = BooleanField(
        "Receive SMS Medication Reminders", default=True
    )
