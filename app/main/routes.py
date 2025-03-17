from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_mail import Message
from flask_login import login_required, login_user
from app.forms import LoginForm  # Import the form class
from app.models import User
from app.application import generate_pdf, db
import traceback


main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()  

    if form.validate_on_submit():
        # Form is valid, authenticate the user
        email = form.email.data
        password = form.password.data
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):  
            login_user(user)
            return redirect(url_for('medicines.my_medicine'))  
        
        flash('Invalid login credentials', 'error')
    
    return render_template('index.html', form=form)


@main_bp.route('/send_pdf/<user_email>')
@login_required
def send_pdf(user_email):
    print(f"Sending PDF to {user_email}")

    pdf_output = generate_pdf()

    # Send the email with the attached PDF
    msg = Message('Your Dose Tracker Report', recipients=[user_email], sender='Dose Tracker <dave@djrogers.net.au>')
    msg.body = 'Please find attached your medicines report.'
    #msg.sender = 'David Rogers'
    
    # Attach the generated PDF
    msg.attach('medicines_report.pdf', 'application/pdf', pdf_output)

    # Send the email
    try:
        if not current_app.extensions['mail']:
            raise ValueError("Mail object is not initialized properly.")
        
        print("Sending email...")
        current_app.extensions['mail'].send(msg)
        print("Email sent!")
        return redirect(url_for('medicines.my_medicine'))
    
    except Exception as e:
        return f"An error occurred: {e}"


@main_bp.route('/test_email')
def test_email():
    msg = Message('Test Email', recipients=['dave@djrogers.net.au'])
    msg.body = 'This is a test email sent from Flask.'
    
    try:
        if not current_app.extensions['mail']:
            raise ValueError("Mail object is not initialized properly.")
        print("Sending email...")
        current_app.extensions['mail'].send(msg)
        print("Email sent!")
        return 'Test email sent successfully!'
    except Exception as e:
        print("Error occurred:", e)
        traceback.print_exc()
        return f"An error occurred: {e}"


