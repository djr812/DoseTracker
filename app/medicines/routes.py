from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Medicine, UserMedicine, MedicationReminder
from app.application import db 
from app.forms import MedicineForm, ReminderForm, EditMedicineForm
from datetime import datetime


# Define the blueprint for medicines routes
medicines = Blueprint('medicines', __name__)


@medicines.route('/api/medicines', methods=['GET'])
@login_required
def api_medicines():
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []
    
    # Fetch associated medicine names and reminders for each user_medicine entry
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)
        
        # Fetch reminders for this user_medicine
        reminders = MedicationReminder.query.filter_by(user_medicine_id=user_medicine.id).all()
        
        # Add reminder details to the medicine data
        reminder_data = []
        for reminder in reminders:
            reminder_data.append({
                'reminder_time': reminder.reminder_time,
                'status': reminder.status
            })
        
        medicines.append({
            'id': medicine.id,
            'name': medicine.name,
            'dosage': user_medicine.dosage,
            'frequency': user_medicine.frequency,
            'notes': user_medicine.notes,
            'reminders': reminder_data  # Include reminder data here
        })
    
    return jsonify(medicines)


# Route for adding a medicine
@medicines.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    medicine_form = MedicineForm()
    reminder_form = ReminderForm()

    if medicine_form.validate_on_submit():
        medicine_name = medicine_form.name.data
        dosage = medicine_form.dosage.data
        frequency = medicine_form.frequency.data
        notes = medicine_form.notes.data

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

            # Create a reminder if reminder details are provided
            if reminder_form.reminder_time.data and reminder_form.reminder_message.data:
                reminder = MedicationReminder(
                    user_id=current_user.id,
                    user_medicine_id=user_medicine.id,
                    reminder_time=reminder_form.reminder_time.data,
                    reminder_message=reminder_form.reminder_message.data,
                    status=reminder_form.status.data  # Using reminder status from the form
                )
                db.session.add(reminder)
                db.session.commit()

            flash('Medicine and reminder added successfully!', 'success')
            return redirect(url_for('medicines.my_medicine'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('add_medicine.html', medicine_form=medicine_form, reminder_form=reminder_form)


# Route for viewing the user's medicines
@medicines.route('/my_medicine')
@login_required
def my_medicine():
    # Query medicines associated with the current user
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []
    
    # Fetch associated medicine names and reminders for each user_medicine entry
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)
        
        # Fetch reminders for this user_medicine
        reminders = MedicationReminder.query.filter_by(user_medicine_id=user_medicine.id).all()
        
        # Format reminder data for template
        reminder_data = []
        for reminder in reminders:
            reminder_data.append({
                'reminder_time': reminder.reminder_time,
                'status': reminder.status
            })
        
        medicines.append({
            'id': medicine.id,
            'name': medicine.name,
            'dosage': user_medicine.dosage,
            'frequency': user_medicine.frequency,
            'notes': user_medicine.notes,
            'reminders': reminder_data  # Add reminders to the template data
    })
    
    return render_template('my_medicine.html', medicines=medicines, page_class='my_medicine_page')


@medicines.route('/delete_medicine/<int:medicine_id>', methods=['POST'])
@login_required
def delete_medicine(medicine_id):
    # Find the record from the user_medicines table
    user_medicine = UserMedicine.query.filter_by(medicine_id=medicine_id, user_id=current_user.id).first()

    if user_medicine is not None:
        # Delete associated reminders for the medicine
        MedicationReminder.query.filter_by(user_medicine_id=user_medicine.id).delete()

        # Delete the user_medicine record
        db.session.delete(user_medicine)
        db.session.commit()
        flash('Medicine deleted successfully!', 'success')
        return redirect(url_for('medicines.my_medicine'))
    else:
        flash('Medicine not found.', 'danger')
        return redirect(url_for('medicines.my_medicine'))


from datetime import datetime

@medicines.route('/edit_medicine/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    user_medicine = UserMedicine.query.filter_by(medicine_id=medicine_id, user_id=current_user.id).first_or_404()
    
    form = EditMedicineForm()

    # ONLY populate form in GET requests
    if request.method == 'GET':
        form.name.data = medicine.name
        form.dosage.data = user_medicine.dosage
        form.frequency.data = user_medicine.frequency
        form.notes.data = user_medicine.notes
        if user_medicine.reminders:
            reminder = user_medicine.reminders[0]
            form.reminder_time.data = reminder.reminder_time
            form.reminder_message.data = reminder.reminder_message
            form.status.data = reminder.status

    if form.validate_on_submit():
        # Update models using form data
        medicine.name = form.name.data.strip()
        user_medicine.dosage = form.dosage.data.strip()
        user_medicine.frequency = form.frequency.data.strip()
        user_medicine.notes = form.notes.data.strip()
        
        # Handle reminder time update
        if form.reminder_time.data:
            try:
                # Check if reminder_time is already a datetime object
                if isinstance(form.reminder_time.data, datetime):
                    reminder_time = form.reminder_time.data
                else:
                    # Convert from string to datetime if it's not already a datetime object
                    reminder_time = datetime.strptime(form.reminder_time.data, '%Y-%m-%dT%H:%M')

                if user_medicine.reminders:
                    reminder = user_medicine.reminders[0]
                    reminder.reminder_time = reminder_time
                    reminder.reminder_message = form.reminder_message.data.strip()
                    reminder.status = form.status.data.strip()
            except ValueError:
                flash('Invalid reminder time format.', 'error')
                return render_template('edit_medicine.html', form=form, medicine=medicine, user_medicine=user_medicine)

        try:
            db.session.commit()
            flash('Changes saved successfully!', 'success')
            return redirect(url_for('medicines.my_medicine'))
        except Exception as e:
            db.session.rollback()
            flash('Update failed. Please try again.', 'error')
            print(f"Database error: {str(e)}")

    return render_template('edit_medicine.html', form=form, medicine=medicine, user_medicine=user_medicine)
