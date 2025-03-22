"""
Filename:   routes.py
Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/main/routes.py

Purpose:    Contains the routes for the main application, including the index route for login
            and a route for sending PDF reports via email. Handles user authentication,
            error messages, and email communication for the Dose Tracker system.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_mail import Message
from flask_login import login_required, login_user
from app.forms import LoginForm
from app.models import User
from app.application import generate_pdf, db
import traceback


main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    """
    Name:       index()
    Purpose:    Handles the user login form submission. It validates the form data, authenticates the
                user based on the provided email and password, and redirects the user to the medicines
                page upon successful login. If login fails, an error message is flashed.
    Parameters: None
    Returns:    Response (Flask): The rendered login page (`index.html`) if the form is not submitted
                or the user is not authenticated, or a redirect to the medicines page if login is
                successful.
    """

    form = LoginForm()

    if form.validate_on_submit():
        # Form is valid, authenticate the user
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("medicines.my_medicine"))

        flash("Invalid login credentials", "error")

    return render_template("index.html", form=form)


@main_bp.route("/send_pdf/<user_email>")
@login_required
def send_pdf(user_email):
    """
    Name:       send_pdf(user_email)
    Purpose:    Generates a PDF report of the user's medicines and sends it via email to the provided
                email address. The function is protected by login requirements to ensure the user is
                authenticated before sending the email.
    Parameters: user_email (str): The email address to which the PDF report will be sent.
    Returns:    Response (Flask): A redirect to the medicines page (`my_medicine`) if the email is
                successfully sent, or an error message if there is a failure during email sending.
    """

    print(f"Sending PDF to {user_email}")

    pdf_output = generate_pdf()

    # Send the email with the attached PDF
    msg = Message(
        "Your Dose Tracker Report",
        recipients=[user_email],
        sender="Dose Tracker <dave@djrogers.net.au>",
    )
    msg.body = "Please find attached your medicines report."

    # Attach the generated PDF
    msg.attach("medicines_report.pdf", "application/pdf", pdf_output)

    # Send the email
    try:
        if not current_app.extensions["mail"]:
            raise ValueError("Mail object is not initialized properly.")

        print("Sending email...")
        current_app.extensions["mail"].send(msg)
        print("Email sent!")
        return redirect(url_for("medicines.my_medicine"))

    except Exception as e:
        return f"An error occurred: {e}"


@main_bp.route("/test_email")
def test_email():
    msg = Message("Test Email", recipients=["dave@djrogers.net.au"])
    msg.body = "This is a test email sent from Flask."

    try:
        if not current_app.extensions["mail"]:
            raise ValueError("Mail object is not initialized properly.")
        print("Sending email...")
        current_app.extensions["mail"].send(msg)
        print("Email sent!")
        return "Test email sent successfully!"
    except Exception as e:
        print("Error occurred:", e)
        traceback.print_exc()
        return f"An error occurred: {e}"
