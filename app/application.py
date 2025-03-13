from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_login import current_user
from config import Config
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from app.models import User, UserMedicine, Medicine
from app.extensions import db, bcrypt


# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()

# Set the login_view to point to your login route
login_manager.login_view = 'auth.login'

def create_app():
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

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints 
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) 
    app.register_blueprint(medicines, url_prefix='/medicines') 

    return app


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
    c.drawImage(logo_path, 30, title_height + 10, width=50, height=50)  # Logo at the top left

    # Set title text color to white for contrast
    c.setFillColor('#FFFFFF')
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, title_height + 25, "Dose Tracker")

    # Query the user's email from the Users table
    user = User.query.get(current_user.id)  # Assuming current_user is properly set
    user_email = user.email if user else 'Unknown'

    # Subtitle: User's Email (Dark grey)
    c.setFillColor('#333333')  # Dark grey color for the email subtitle
    c.setFont("Helvetica", 12)
    c.drawString(100, title_height - title_margin, f"Report for: {user_email}")

    # Line separation for clarity
    c.line(30, title_height - title_margin - 10, 580, title_height - title_margin - 10)

    # Set up the table header with a background color
    c.setFillColor('#9b4d96')  # Mauve for the table header background
    c.rect(30, 670, 540, 20, fill=1)  # Draw header background

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