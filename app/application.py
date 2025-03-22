"""
application.py
-------------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/application.py

Purpose:    Initializes and configures the Flask application, including setting up extensions,
            database models, routes, and scheduled tasks like daily medication reminders and SMS alerts.
"""

from flask import Flask, current_app
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail, Message
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from config import Config
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from app.models import User, UserMedicine, Medicine, MedicationReminder
from app.extensions import db, bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from twilio.rest import Client
from datetime import datetime
from pytz import timezone


# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()

# Set the login_view to point to the login route
login_manager.login_view = "auth.login"

# Initialize the scheduler
scheduler = BackgroundScheduler(timezone=timezone("Australia/Brisbane"))


def create_app():
    """
    Name:       create_app()
    Purpose:    Initializes the Flask application, configures extensions (SQLAlchemy, Flask-Mail, etc.),
                sets up routes using Blueprints, and starts the APScheduler for daily medication reminders.
    Parameters: None
    Returns:    app (Flask): The initialized Flask application instance.
    """
    print("Creating app...")
    # Initialise the Flask app
    app = Flask(__name__)

    # App configuration
    app.config.from_object("config.Config")

    # Configure Flask-Mail
    app.config["MAIL_SERVER"] = "mx3594.syd1.mymailhosting.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = "dave@djrogers.net.au"
    app.config["MAIL_PASSWORD"] = Config.MAIL_SERVER_PASS
    app.config["MAIL_DEFAULT_SENDER"] = "dave@djrogers.net.au"

    # Initialise Mail
    mail = Mail(app)

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import models and routes after extensions are initialized
    with app.app_context():
        from .models import User
        from .auth.routes import auth_bp
        from .main.routes import main_bp
        from .medicines.routes import medicines

    # Initialise CSRF instance
    csrf = CSRFProtect(app)

    # Configure login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(medicines, url_prefix="/medicines")

    # Create daily job-creation job
    scheduler.add_job(
        schedule_daily_reminders,
        CronTrigger(hour=1, minute=0),  # Trigger at 1:00 AM every day
        args=[app, mail],
    )

    # Start APScheduler
    scheduler.start()

    return app


def schedule_daily_reminders(app, mail):
    """
    Name:       schedule_daily_reminders(app, mail)
    Purpose:    Resets the status of all medication reminders to 'pending', groups reminders by time,
                and schedules SMS reminders for each user at the appropriate time using APScheduler.
    Parameters: app (Flask): The Flask application instance.
                mail (Mail): The Flask-Mail instance used to send email notifications.
    Returns:    None
    """

    with app.app_context():
        # Reset the status of all reminders to 'pending'
        db.session.query(MedicationReminder).update(
            {MedicationReminder.status: "pending"}
        )
        db.session.commit()

        # Query all reminders for today that need to be sent
        meds_today = (
            db.session.query(MedicationReminder)
            .filter(MedicationReminder.reminder_time >= datetime.now().time())
            .all()
        )
        print("Schedule Jobs for today")

        # Group reminders by their reminder time
        reminders_by_time = {}
        for med in meds_today:
            reminder_time = med.reminder_time
            if reminder_time not in reminders_by_time:
                reminders_by_time[reminder_time] = []
            reminders_by_time[reminder_time].append(med)

        print(reminders_by_time)

        # For each unique reminder time, schedule an SMS job
        for reminder_time, meds in reminders_by_time.items():
            for med in meds:
                user = med.user
                # Skip users who opted out of SMS reminders
                if not user.receive_sms_reminders:
                    continue

                # Schedule a job to send the SMS for that reminder time
                scheduler.add_job(
                    send_sms,
                    CronTrigger(hour=reminder_time.hour, minute=reminder_time.minute),
                    args=[(reminder_time, meds, app)],
                    id=f"send_sms_{reminder_time.hour}_{reminder_time.minute}",
                    name=user.email,
                    replace_existing=True,
                )

        # Collect job information to send in an email
        job_info = []
        jobs = scheduler.get_jobs()
        for job in jobs:
            trigger = job.trigger
            if isinstance(trigger, CronTrigger):
                job_info.append(
                    f"Name: {job.name}, Job ID: {job.id}, Next Run Time: {job.next_run_time} \n"
                )

        # Format the job information into a string
        job_info_str = "\n".join(job_info)

        # Send the job info via email
        try:
            msg = Message(
                "Scheduled Daily Reminders", recipients=["dave@djrogers.net.au"]
            )
            msg.body = f"The following jobs were scheduled for today:\n\n{job_info_str}"
            mail.send(msg)
            print("Job information sent via email.")
        except Exception as e:
            print(f"Error sending email: {e}")


def send_sms(job_data):
    """
    Name:       send_sms(job_data)
    Purpose:    Sends an SMS reminder to the user for a scheduled medication reminder using the Twilio API.
                Updates the status of the medication reminders to 'sent' once the SMS is successfully delivered.
    Parameters: job_data (tuple): A tuple containing the reminder time, list of medications, and Flask app instance.
    Returns:    None
    """
    reminder_time, meds, app = job_data

    with app.app_context():
        # Initialise Twilio client
        twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

        message_body = "DoseTracker Reminder: "
        for med in meds:
            message_body += f"{med.reminder_message}\n"

        # Retrieve the user's phone number from the database
        user = User.query.get(meds[0].user_id)
        if user and user.phone_number:
            # remove the leading '0' in the mobile number
            if user.phone_number.startswith("0"):
                user_phone_number = user.phone_number[1:]
            # add +61 country code
            user_phone_number = f"+61 {user_phone_number}"
        else:
            print("User phone number is missing.")
            return

        # Send the reminder via Twilio SMS
        try:
            if message_body:
                twilio_client.messages.create(
                    body=message_body,
                    from_=Config.TWILIO_PHONE_NUMBER,
                    to=user_phone_number,
                )

            print(
                f"Sent reminder ({message_body}) for {reminder_time} to {user_phone_number}"
            )

            # Set the medication status to 'sent'
            try:
                for med in meds:
                    med.status = "sent"
                db.session.commit()
                print(f"Updated status to 'sent' for {len(meds)} medications.")
            except Exception as e:
                print(f"Error updating status: {e}")

        except Exception as e:
            print(f"Error sending SMS for {reminder_time} to {user_phone_number}: {e}")


def generate_pdf():
    """
    Name:       generate_pdf()
    Purpose:    Generates a PDF report for the logged-in user, including a list of their medications,
                using the ReportLab library. The PDF includes a title, user's email, and a table of medication details.
    Parameters: None
    Returns:    pdf_data (bytes): The generated PDF content as bytes.
    """

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Title and logo area
    title_height = 720
    title_margin = 20

    # Set title background colour (mauve)
    c.setFillColor("#9b4d96")
    c.rect(0, title_height, 600, 80, fill=1)

    # Add the logo
    logo_path = "app/static/img/logo.png"
    c.drawImage(logo_path, 30, title_height + 10, width=55, height=50)

    # Set title text colour to white for contrast
    c.setFillColor("#FFFFFF")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, title_height + 25, "Dose Tracker")

    # Query the user's email from the Users table
    user = User.query.get(current_user.id)
    user_email = user.email if user else "Unknown"

    # Subtitle: User's Email (Dark grey)
    c.setFillColor("#333333")
    c.setFont("Helvetica", 12)
    c.drawString(100, title_height - title_margin, f"Report for: {user_email}")

    # Set up the table header with a background colour (Mauve)
    c.setFillColor("#9b4d96")
    c.rect(30, 670, 540, 20, fill=1)

    # Table header text (white)
    c.setFillColor("#FFFFFF")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, 675, "Name")
    c.drawString(150, 675, "Dosage")
    c.drawString(250, 675, "Frequency")
    c.drawString(350, 675, "Notes")

    # Set the font for table content (Black)
    c.setFillColor("#000000")
    c.setFont("Helvetica", 10)

    # Query medicines associated with the current user
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []

    # Fetching associated medicine names for each user_medicine entry
    y_position = 650
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)
        medicines.append(
            {
                "name": medicine.name,
                "dosage": user_medicine.dosage,
                "frequency": user_medicine.frequency,
                "notes": user_medicine.notes or "N/A",
            }
        )

        # Add medicine data to the table
        c.drawString(30, y_position, medicine.name)
        c.drawString(150, y_position, user_medicine.dosage)
        c.drawString(250, y_position, user_medicine.frequency)
        c.drawString(350, y_position, user_medicine.notes or "N/A")

        y_position -= 20  # Move to the next row

        # Check if the y_position is too low, and create a new page if necessary
        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor("#9b4d96")
            c.rect(30, 670, 540, 20, fill=1)
            c.setFillColor("#FFFFFF")
            c.drawString(30, 675, "Name")
            c.drawString(150, 675, "Dosage")
            c.drawString(250, 675, "Frequency")
            c.drawString(350, 675, "Notes")
            c.setFont("Helvetica", 10)
            y_position = 650  # Reset the y_position for the new page

    # Save the PDF to the buffer
    c.save()

    # Get the PDF content as bytes
    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data
