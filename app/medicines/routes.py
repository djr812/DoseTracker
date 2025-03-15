from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Medicine, UserMedicine
from app.application import db


# Define the blueprint for medicines routes
medicines = Blueprint('medicines', __name__)


@medicines.route('/api/medicines', methods=['GET'])
@login_required
def api_medicines():
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []
    
    # Fetch associated medicine names for each user_medicine entry
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)
        medicines.append({
            'id': medicine.id,
            'name': medicine.name,
            'dosage': user_medicine.dosage,
            'frequency': user_medicine.frequency,
            'notes': user_medicine.notes
        })
    
    return jsonify(medicines)


# Route for adding a medicine
@medicines.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        medicine_name = request.form.get('name')
        dosage = request.form.get('dosage')
        frequency = request.form.get('frequency')
        notes = request.form.get('notes')

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
            frequency=frequency,
            notes=notes
        )

        try:
            db.session.add(user_medicine)
            db.session.commit()
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('medicines.my_medicine'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('add_medicine.html')


# Route for viewing the user's medicines
@medicines.route('/my_medicine')
@login_required
def my_medicine():
    # Query medicines associated with the current user
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []
    
    # Fetching associated medicine names for each user_medicine entry
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)
        medicines.append({
            'id': medicine.id,
            'name': medicine.name,
            'dosage': user_medicine.dosage,
            'frequency': user_medicine.frequency,
            'notes': user_medicine.notes
        })
    
    return render_template('my_medicine.html', medicines=medicines, page_class='my_medicine_page')


@medicines.route('/delete_medicine/<int:medicine_id>', methods=['DELETE'])
@login_required
def delete_medicine(medicine_id):
    # Find the record from the user_medicines table
    user_medicine = UserMedicine.query.filter_by(medicine_id=medicine_id, user_id=current_user.id).first()
    
    if user_medicine is not None:
        db.session.delete(user_medicine)
        db.session.commit()
        return jsonify({'message': 'Medicine deleted successfully'}), 200
    else:
        return jsonify({'message': 'Medicine not found'}), 404


@medicines.route('/edit_medicine/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(medicine_id):
    try:
        # Retrieve the medicine from the database based on its ID
        medicine = Medicine.query.get_or_404(medicine_id)
    except Exception as e:
        # Log the error if medicine is not found
        print(f"Error retrieving medicine with ID {medicine_id}: {e}")
        return "Error: Medicine not found", 404
    
    user_medicine = UserMedicine.query.filter_by(medicine_id=medicine_id).first()

    if user_medicine is None:
        # Handle the case where the user doesn't have a UserMedicine entry
        return render_template('edit_medicine.html', error="Medicine data not found.")

    if request.method == 'POST':
        # Get the updated details from the form
        medicine.name = request.form['name']
        user_medicine.dosage = request.form['dosage']
        user_medicine.frequency = request.form['frequency']
        user_medicine.notes = request.form['notes']
        
        # Save the updated medicine details to the database
        try:
            db.session.commit()
            return redirect(url_for('medicines.my_medicine'))  # Redirect to a page showing all medicines
        except Exception as e:
            db.session.rollback()  # Rollback on error
            print(f"Error during commit: {e}")
            return render_template('edit_medicine.html', medicine=medicine, user_medicine=user_medicine, error="Error updating medicine.")


    # If the method is GET, render the form with the existing medicine data
    return render_template('edit_medicine.html', medicine=medicine, user_medicine=user_medicine)
