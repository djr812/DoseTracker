from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.application import db, bcrypt
from flask_login import login_user, login_required
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            # Login the user and redirect to dashboard
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  
        else:
            flash('Invalid login credentials', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('index.html')

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

    return render_template('sign_up.html')
