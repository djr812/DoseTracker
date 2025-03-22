"""
routes.py
-------------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/auth/routes.py

Purpose:    Contains routes related to user authentication, registration, password reset,
            and account management. Handles user login, logout, sign-up, password recovery,
            and the user admin page for updating user information and preferences like SMS reminders.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from app.application import db
from flask_bcrypt import Bcrypt
from flask_mail import Message
from flask_login import login_user, login_required, current_user, logout_user
from app.models import User
from app.forms import (
    LoginForm,
    SignUpForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    UserAdminForm,
)
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from urllib.parse import quote_plus, unquote_plus


auth_bp = Blueprint("auth", __name__)

SECRET_KEY = current_app.config["SECRET_KEY"]
s = Serializer(SECRET_KEY)

bcrypt = Bcrypt()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Name:       login()
    Purpose:    Handles user login, validates credentials, and manages user session.
                If the user is already logged in, redirects to the medicine page.
                If login is successful, redirects the user to their medicine list.
                If login fails, displays an error message.
    Parameters: None
    Returns:    Response: A rendered template of the login page or a redirect to the medicine page.
    """
    # If the user is already logged in, redirect them to /my_medicine
    if current_user.is_authenticated:
        return redirect(url_for("medicines.my_medicine"))

    form = LoginForm()  # Create a form instance

    if form.validate_on_submit():  # This handles both POST and form validation
        email = form.email.data  # Get the email from the form
        password = form.password.data  # Get the password from the form

        # Find the user by email
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):  # Check credentials
            login_user(user, remember=True)
            flash("You have been logged in!", "success")
            return redirect(
                url_for("medicines.my_medicine")
            )  # Redirect to the medicines page

        else:
            flash(
                "Invalid credentials, please try again", "danger"
            )  # Flash error if login fails

    return render_template(
        "index.html", form=form, page_class="index_page"
    )  # Pass the form to the template


@auth_bp.route("/logout")
def logout():
    """
    Name:       logout()
    Purpose:    Logs the user out of the application by clearing their session and
                redirecting them to the login page. Displays a success message
                after logout.
    Parameters: None
    Returns:    Response: A redirect to the login page with a flash message indicating successful logout.
    """
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    """
    Name:       sign_up()
    Purpose:    Handles the user sign-up process, including form validation,
                checking for existing users, hashing passwords, and adding
                new users to the database. After a successful sign-up, redirects
                the user to the login page with a success message.
    Parameters: None
    Returns:    Response: Renders the sign-up page with the form, or redirects
                           the user to the login page after a successful sign-up.
    """
    form = SignUpForm()

    if form.validate_on_submit():
        # Retrieve form data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        phone_number = form.phone_number.data

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already taken. Please choose another.", "danger")
            return redirect(url_for("auth.sign_up"))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Create new user
        new_user = User(
            email=email, password_hash=hashed_password, phone_number=phone_number
        )

        # Add user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Sign-up successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
            return redirect(url_for("auth.sign_up"))

    return render_template("sign_up.html", form=form, page_class="sign_up_page")


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """
    Name:       forgot_password()
    Purpose:    Handles the forgot password process, including form validation,
                checking if the email exists in the system, generating a password
                reset token, and sending a password reset link to the user's email.
                Redirects the user to the login page after sending the reset email.
    Parameters: None
    Returns:    Response: Renders the forgot password page with the form or
                           redirects the user with a flash message indicating
                           whether the email was found or not.
    """
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            # Create the reset token
            token = s.dumps(email, salt="reset-password")
            token = quote_plus(token)
            reset_link = url_for("auth.reset_password", token=token, _external=True)

            # Send the reset password link via email
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_link}"
            current_app.extensions["mail"].send(msg)

            flash("Check your email for a password reset link!", "info")
            return redirect(url_for("auth.login"))
        else:
            flash("Email address not found in our system.", "warning")

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Name:       reset_password(token)
    Purpose:    Handles the password reset process by verifying the reset token,
                loading the user's email, and allowing the user to submit a new password.
                It ensures that the token is valid and not expired. After successful
                password reset, it redirects the user to the login page.
    Parameters: token (str): The token generated for the password reset request.
    Returns:    Response: Renders the reset password page with the form or
                           redirects the user with a flash message indicating
                           the token's validity and the result of the reset process.
    """

    try:
        email = s.loads(
            token, salt="reset-password", max_age=3600
        )  # Token valid for 1 hour
    except SignatureExpired:
        flash("The reset link has expired.", "danger")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("Invalid or tampered reset link.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        new_password = form.password.data
        # Hash the new password using bcrypt
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

        # Update the user's password in the database
        user.password_hash = hashed_password
        db.session.commit()

        flash("Your password has been reset successfully.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form, token=token)


@auth_bp.route("/user-admin", methods=["GET", "POST"])
@login_required
def user_admin():
    """
    Name:       user_admin()
    Purpose:    Provides the user with the ability to update their phone number
                and SMS reminder preferences. It pre-fills the form with the
                current user's information and allows them to submit changes.
                Updates are committed to the database, and any errors during the
                process are handled appropriately.
    Parameters: None
    Returns:    Response: Renders the user admin page with the form, or redirects
                           the user with a flash message indicating the success or failure
                           of the update process.
    """

    form = UserAdminForm()

    # Pre-fill the form with current user data
    if request.method == "GET":
        form.phone_number.data = current_user.phone_number
        form.receive_sms_reminders.data = current_user.receive_sms_reminders

    if form.validate_on_submit():
        # Update user information
        current_user.phone_number = form.phone_number.data
        current_user.receive_sms_reminders = form.receive_sms_reminders.data

        try:
            db.session.commit()
            flash("Your information has been updated!", "success")
            return redirect(url_for("medicines.my_medicine"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
            return redirect(url_for("auth.user_admin"))  # Redirect to the same page

    return render_template("user_admin.html", form=form)
