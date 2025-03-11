from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Medicine, UserMedicine
from app.application import db

# Define the blueprint for medicines routes
medicines = Blueprint('medicines', __name__)

# Route for adding a medicine
@medicines.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name')
        dosage = request.form.get('dosage')
        frequency = request.form.get('frequency')

        # Find the medicine in the database or create it
        medicine = Medicine.query.filter_by(name=medicine_name).first()
        if not medicine:
            medicine = Medicine(name=medicine_name)
            db.session.add(medicine)
            db.session.commit()

        # Add the medicine to the user's list
        user_medicine = UserMedicine(
            user_id=current_user.id,
            medicine_id=medicine.id,
            dosage=dosage,
            frequency=frequency
        )

        try:
            db.session.add(user_medicine)
            db.session.commit()
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('medicines.view_medicines'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('add_medicine.html')

# Route for viewing the user's medicines
@medicines.route('/my_medicines')
@login_required
def view_medicines():
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    return render_template('my_medicines.html', user_medicines=user_medicines)
