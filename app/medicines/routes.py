from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Medicine, UserMedicine, MedicationReminder
from app.application import db 
from app.forms import MedicineForm, ReminderForm, EditMedicineForm
from datetime import time, datetime
from wtforms import TimeField, StringField, SelectField
import wikipediaapi


# Define the blueprint for medicines routes
medicines = Blueprint('medicines', __name__)

# Initialise Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(user_agent='DoseTracker (dave@djrogers.net.au)', language='en')


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

    if request.method == 'POST':
        # Debugging - check reminder times and messages manually
        print("Frequency:", medicine_form.frequency.data)
        # Loop through dynamically generated reminder fields
        reminder_count = get_reminder_count(medicine_form.frequency.data)
        for i in range(reminder_count):
            reminder_time = request.form.get(f'reminder_time_{i}')
            reminder_message = request.form.get(f'reminder_message_{i}')
            print(f"Reminder {i+1} Time: {reminder_time}")
            print(f"Reminder {i+1} Message: {reminder_message}")

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
        db.session.add(user_medicine)
        db.session.commit()

        # Create a reminder if reminder details are provided
        reminder_count = get_reminder_count(frequency)
        for i in range(reminder_count):
            reminder_time = request.form.get(f'reminder_time_{i}')
            reminder_message = request.form.get(f'reminder_message_{i}')
            status = reminder_form.status.data  # Using status from the form

            print(f"Reminder {i+1} Time:", reminder_time)
            print(f"Reminder {i+1} Message:", reminder_message)

            if reminder_time and reminder_message:
                reminder = MedicationReminder(
                    user_id=current_user.id,
                    user_medicine_id=user_medicine.id,
                    reminder_time=reminder_time,
                    reminder_message=reminder_message,
                    status=status
                )
                db.session.add(reminder)

        try:
            db.session.commit()
            flash('Medicine and reminder added successfully!', 'success')
            return redirect(url_for('medicines.my_medicine'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('add_medicine.html', medicine_form=medicine_form, reminder_form=reminder_form)


def get_reminder_count(frequency):
    if frequency == 'Once a Day':
        return 1
    elif frequency == 'Twice a Day':
        return 2
    elif frequency == 'Three Times a Day':
        return 3
    elif frequency == 'Four Times a Day':
        return 4
    return 0  # Default to 0 if no frequency is matched


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
    
    # Sort medicines by the first reminder time, then by medicine name
    medicines.sort(key=lambda x: (
        x['reminders'][0]['reminder_time'] if x['reminders'] else time.min,  # Use time.min for empty reminders
        x['name']
    ))

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


@medicines.route('/edit_medicine/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(medicine_id):
    # Retrieve the medicine and user_medicine from the database
    medicine = Medicine.query.get_or_404(medicine_id)
    user_medicine = UserMedicine.query.filter_by(medicine_id=medicine_id, user_id=current_user.id).first_or_404()

    # Create the form
    form = EditMedicineForm()

    # Handle GET request to pre-fill the form with current data
    if request.method == 'GET':
        form.name.data = medicine.name
        form.dosage.data = user_medicine.dosage
        form.frequency.data = user_medicine.frequency
        form.notes.data = user_medicine.notes

        # Prepare reminder data for JavaScript
        reminder_data = []
        if user_medicine.reminders:
            for reminder in user_medicine.reminders:
                reminder_data.append({
                    'reminder_time': reminder.reminder_time.strftime('%H:%M') if reminder.reminder_time else '',
                    'reminder_message': reminder.reminder_message or '',
                    'status': reminder.status or 'pending'
                })

        return render_template('edit_medicine.html', form=form, medicine=medicine, user_medicine=user_medicine, reminder_data=reminder_data)

    # Handle POST request for form submission
    if request.method == 'POST':
        # Extract reminder data from the form dynamically based on the number of reminders
        reminder_times = [request.form.get(f'reminder_time_{i}') for i in range(4)]  # Max 4 reminders
        reminder_messages = [request.form.get(f'reminder_message_{i}') for i in range(4)]
        statuses = [request.form.get(f'status_{i}') for i in range(4)]

        # Debugging: Print reminder data and status
        print(f"Reminder Times: {reminder_times}")
        print(f"Reminder Messages: {reminder_messages}")
        print(f"Statuses: {statuses}")
        print(f"User ID: {current_user.id}")

        # Manually validate statuses
        valid_status_choices = ['pending', 'sent']
        statuses = [status if status in valid_status_choices else 'pending' for status in statuses]

        # Filter out empty reminder data
        filtered_reminders = [
            (time, message, status)
            for time, message, status in zip(reminder_times, reminder_messages, statuses)
            if time and message and status in valid_status_choices
        ]

        # Check if the form is valid
        if form.validate_on_submit():
            # Update basic medicine data
            medicine.name = form.name.data.strip()
            user_medicine.dosage = form.dosage.data.strip()
            user_medicine.frequency = form.frequency.data.strip()
            user_medicine.notes = form.notes.data.strip()

            # Get the current reminders
            current_reminders = user_medicine.reminders

            # If the number of reminders has decreased, delete the extra ones from the database
            if len(filtered_reminders) < len(current_reminders):
                # Remove excess reminders
                for i in range(len(filtered_reminders), len(current_reminders)):
                    db.session.delete(current_reminders[i])

            # Loop over the filtered reminder fields and update or create new reminders
            for i, (reminder_time, reminder_message, status) in enumerate(filtered_reminders):
                if i < len(current_reminders):
                    reminder = current_reminders[i]  # Update existing reminder
                    reminder.reminder_time = reminder_time
                    reminder.reminder_message = reminder_message
                    reminder.status = status
                else:
                    # If no reminder exists, create a new reminder
                    new_reminder = MedicationReminder(
                        reminder_time=reminder_time,
                        reminder_message=reminder_message,
                        status=status,
                        user_medicine_id=user_medicine.id,  # Ensure user_medicine_id is set correctly
                        user_id=current_user.id  # Ensure user_id is set correctly here
                    )
                    db.session.add(new_reminder)

            # Commit changes to the database
            try:
                db.session.commit()
                flash('Changes saved successfully!', 'success')
                return redirect(url_for('medicines.my_medicine'))
            except Exception as e:
                db.session.rollback()
                flash('Update failed. Please try again.', 'error')
                print(f"Error: {e}")
        else:
            flash("Form validation failed", "error")
            print("Form validation failed. Errors:", form.errors)

    return render_template('edit_medicine.html', form=form, medicine=medicine, user_medicine=user_medicine, reminder_data=[])


@medicines.route('/medicine/<int:medicine_id>', methods=['GET'])
@login_required
def medicine_details(medicine_id):
    # Query the medicine from the database
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return "Medicine not found", 404
    
    # Use wikipedia-api to search for the medicine
    page = wiki_wiki.page(medicine.name)
    
    # Check if the page exists
    if not page.exists():
        return "Wikipedia page not found for this medicine", 404
    
    # Get the sections from the Wikipedia page
    sections = []
    for section in page.sections:
        sections.append({
            'title': section.title,
            'content': section.text[:500],  # Just show the first 500 characters initially
            'full_content': section.text  # The full content for later expansion
        })
    
    return render_template('medicine_details.html', medicine=medicine, sections=sections)