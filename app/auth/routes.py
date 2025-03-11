from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.application import db, bcrypt
from flask_login import login_user, login_required, current_user, logout_user
from app.models import User


auth_bp = Blueprint('auth', __name__)

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect them to /my_medicine
    if current_user.is_authenticated:
        return redirect(url_for('medicines.my_medicine'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find the user by email
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):  
            # Log the user in
            login_user(user, remember=True)

            # Redirect to the my_medicine page after successful login
            return redirect(url_for('medicines.my_medicine'))

        else:
            flash('Invalid credentials, please try again', 'danger')

    return render_template('index.html', page_class='index_page')


# Logout Route
@auth_bp.route('/logout')
def logout():
    logout_user()  
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))  


# Sign up Route
@auth_bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # Retrieve form data
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already taken. Please choose another.', 'danger')
            return redirect(url_for('auth.sign_up'))

        # Ensure passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('auth.sign_up'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create new user
        new_user = User(email=email, password_hash=hashed_password)

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

    return render_template('sign_up.html', page_class='sign_up_page')
