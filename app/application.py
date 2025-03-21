from flask import Flask, current_app
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
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

# Set the login_view to point to your login route
login_manager.login_view = 'auth.login'

# Initialize the scheduler
scheduler = BackgroundScheduler(timezone=timezone('Australia/Brisbane'))

def create_app():
    print("Creating app...")
    # Initialize the Flask app
    app = Flask(__name__)

    # App configuration
    app.config.from_object('config.Config')

    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = 'mx3594.syd1.mymailhosting.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'dave@djrogers.net.au'
    app.config['MAIL_PASSWORD'] = Config.MAIL_SERVER_PASS
    app.config['MAIL_DEFAULT_SENDER'] = 'dave@djrogers.net.au'
    
    # Initialize Mail
    mail = Mail(app)
    
    # Initialize extensions
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

    csrf = CSRFProtect(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints 
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) 
    app.register_blueprint(medicines, url_prefix='/medicines') 

    scheduler.add_job(
        schedule_daily_reminders,
        CronTrigger(hour=12, minute=45),  # Trigger at 1:00 AM every day
        args=[app],
    )
    
    # Start APScheduler
    scheduler.start()

    return app


# Job function to schedule SMS reminders for all users
def schedule_daily_reminders(app):
    with app.app_context():
        # Reset the status of all reminders to 'pending'
        db.session.query(MedicationReminder).update({MedicationReminder.status: 'pending'})
        db.session.commit() 
        
        # Query all reminders for today that need to be sent
        meds_today = db.session.query(MedicationReminder).filter(
            MedicationReminder.reminder_time >= datetime.now().time()
        ).all()
        print('Schedule Jobs for today')
        # Group reminders by their reminder time
        reminders_by_time = {}
        for med in meds_today:
            reminder_time = med.reminder_time
            if reminder_time not in reminders_by_time:
                reminders_by_time[reminder_time] = []
            reminders_by_time[reminder_time].append(med)
        
        print(reminder_time, reminders_by_time)

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
                    CronTrigger(hour=reminder_time.hour, minute=reminder_time.minute),  # Schedule job at reminder time
                    args=[(reminder_time, meds, app)],  # Pass reminder time and list of medications
                    id=f"send_sms_{reminder_time.hour}_{reminder_time.minute}",  # Ensure unique job ID
                    replace_existing=True  # Replace any existing jobs for the same time
                )
        # Print the currently scheduled jobs
        jobs = scheduler.get_jobs()
        for job in jobs:
            print(f"Job ID: {job.id}, Next Run Time: {job.next_run_time}, Trigger: {job.trigger}")


def send_sms(job_data):
    reminder_time, meds, app = job_data

    with app.app_context():
        # Initialize Twilio client
        twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        message_body = "DoseTracker Reminder: "
        for med in meds:
            message_body += f"{med.reminder_message}\n"

        # Retrieve the user's phone number from the database
        user = User.query.get(meds[0].user_id)  
        if user and user.phone_number:
            if user.phone_number.startswith('0'):
                user_phone_number = user.phone_number[1:]
            # add +61 country code
            user_phone_number = f"+61 {user_phone_number}"
        else:
            print("User phone number is missing.")
            return

        try:
            if message_body:
                twilio_client.messages.create(
                    body=message_body,
                    from_=Config.TWILIO_PHONE_NUMBER,
                    to=user_phone_number
                )
                
            print(f"Sent reminder ({message_body}) for {reminder_time} to {user_phone_number}")

            try:
                for med in meds:
                    med.status = 'sent'
                db.session.commit()  
                print(f"Updated status to 'sent' for {len(meds)} medications.")
            except Exception as e:
                print(f"Error updating status: {e}")
        
        except Exception as e:
            print(f"Error sending SMS for {reminder_time} to {user_phone_number}: {e}")


def generate_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Title and logo area
    title_height = 720
    title_margin = 20

    # Set title background color (mauve)
    c.setFillColor('#9b4d96')
    c.rect(0, title_height, 600, 80, fill=1)  # Fill a rectangle for the title background

    # Add the logo
    logo_path = "app/static/img/logo.png"  # Adjust the path to your static folder location
    c.drawImage(logo_path, 30, title_height + 10, width=55, height=50)  # Logo at the top left

    # Set title text color to white for contrast
    c.setFillColor('#FFFFFF')
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, title_height + 25, "Dose Tracker")

    # Query the user's email from the Users table
    user = User.query.get(current_user.id)  
    user_email = user.email if user else 'Unknown'
    
    # Subtitle: User's Email (Dark grey)
    c.setFillColor('#333333')  # Dark grey color for the email subtitle
    c.setFont("Helvetica", 12)
    c.drawString(100, title_height - title_margin, f"Report for: {user_email}")

    # Set up the table header with a background color
    c.setFillColor('#9b4d96')  # Mauve for the table header background
    c.rect(30, 670, 540, 20, fill=1)  

    # Table header text (white)
    c.setFillColor('#FFFFFF')
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, 675, "Name")
    c.drawString(150, 675, "Dosage")
    c.drawString(250, 675, "Frequency")
    c.drawString(350, 675, "Notes")

    # Set the font for table content (Black)
    c.setFillColor('#000000')
    c.setFont("Helvetica", 10)

    # Query medicines associated with the current user
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []

    # Fetching associated medicine names for each user_medicine entry
    y_position = 650  # Start position for the table rows
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)
        medicines.append({
            'name': medicine.name,
            'dosage': user_medicine.dosage,
            'frequency': user_medicine.frequency,
            'notes': user_medicine.notes or 'N/A'
        })
        
        # Add medicine data to the table
        c.drawString(30, y_position, medicine.name)
        c.drawString(150, y_position, user_medicine.dosage)
        c.drawString(250, y_position, user_medicine.frequency)
        c.drawString(350, y_position, user_medicine.notes or 'N/A')

        y_position -= 20  # Move to the next row

        # Check if the y_position is too low, and create a new page if necessary
        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor('#9b4d96')
            c.rect(30, 670, 540, 20, fill=1)  # Draw header background again
            c.setFillColor('#FFFFFF')
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




