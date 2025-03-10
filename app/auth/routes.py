from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.application import db, bcrypt
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
            return redirect(url_for('dashboard'))  # Adjust accordingly
        else:
            flash('Invalid login credentials', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('index.html')

# Sign up Route
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create a new user
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.login'))  # Redirect to login page after signup

    return render_template('signup.html')  # Render a signup form (you'll need to create this page)
