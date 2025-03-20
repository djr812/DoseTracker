from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.application import db
from flask_bcrypt import Bcrypt
from flask_mail import Message
from flask_login import login_user, login_required, current_user, logout_user
from app.models import User
from app.forms import LoginForm, SignUpForm, ForgotPasswordForm, ResetPasswordForm
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from urllib.parse import quote_plus, unquote_plus


auth_bp = Blueprint('auth', __name__)

SECRET_KEY = current_app.config['SECRET_KEY']
s = Serializer(SECRET_KEY)

bcrypt = Bcrypt()

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect them to /my_medicine
    if current_user.is_authenticated:
        return redirect(url_for('medicines.my_medicine'))
    
    form = LoginForm()  # Create a form instance

    if form.validate_on_submit():  # This handles both POST and form validation
        email = form.email.data  # Get the email from the form
        password = form.password.data  # Get the password from the form

        # Find the user by email
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):  # Check credentials
            login_user(user, remember=True)
            flash('You have been logged in!', 'success')
            return redirect(url_for('medicines.my_medicine'))  # Redirect to the medicines page

        else:
            flash('Invalid credentials, please try again', 'danger')  # Flash error if login fails

    return render_template('index.html', form=form, page_class='index_page')  # Pass the form to the template


# Logout Route
@auth_bp.route('/logout')
def logout():
    logout_user()  
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))  


# Sign up Route
@auth_bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
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
            flash('Email is already taken. Please choose another.', 'danger')
            return redirect(url_for('auth.sign_up'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Remove leading zero from mobile number
        if phone_number.startswith('0'):
            phone_number = phone_number[1:]

        # Create new user
        new_user = User(email=email, password_hash=hashed_password, phone_number=phone_number)

        # Add user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Sign-up successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')
            return redirect(url_for('auth.sign_up'))

    return render_template('sign_up.html', form=form, page_class='sign_up_page')


# Forgotten Password route
@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Create the reset token
            token = s.dumps(email, salt='reset-password')
            token = quote_plus(token)
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            
            # Send the reset password link via email
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'Click the link to reset your password: {reset_link}'
            current_app.extensions['mail'].send(msg)
            
            flash('Check your email for a password reset link!', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Email address not found in our system.', 'warning')
    
    return render_template('forgot_password.html', form=form)


# Reset Password route
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=3600)  # Token valid for 1 hour
    except SignatureExpired:
        flash("The reset link has expired.", 'danger')
        return redirect(url_for('auth.login'))
    except BadSignature:
        flash("Invalid or tampered reset link.", 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        new_password = form.password.data
        # Hash the new password using bcrypt
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        # Update the user's password in the database
        user.password_hash = hashed_password
        db.session.commit()  # Commit the change

        flash("Your password has been reset successfully.", 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form, token=token)