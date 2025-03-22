"""
medicines/routes.py
--------------------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/medicines/routes.py
Purpose:    Contains the routes related to managing medicines for the user, including adding,
            editing, and deleting medicines. It also handles reminders, querying associated
            medicines, and generating medicine details from external sources such as Wikipedia.

            The routes allow users to view and interact with their medicines, set medication
            reminders, and access additional information about each medicine.
Routes:
    - /api/medicines: Provides a JSON representation of the user's medicines and associated reminders.
    - /add_medicine: Allows users to add new medicines and set up reminders.
    - /my_medicine: Displays a list of the user's medicines along with their reminders.
    - /delete_medicine/<medicine_id>: Deletes a specific medicine from the user's list.
    - /edit_medicine/<medicine_id>: Enables users to edit the details of an existing medicine and its reminders.
    - /medicine/<medicine_id>: Fetches and displays detailed information about a medicine, including content from Wikipedia.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Medicine, UserMedicine, MedicationReminder
from app.application import db
from app.forms import MedicineForm, ReminderForm, EditMedicineForm
from datetime import time, datetime
from wtforms import TimeField, StringField, SelectField
import wikipediaapi


# Define the blueprint for medicines routes
medicines = Blueprint("medicines", __name__)

# Initialise Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent="DoseTracker (dave@djrogers.net.au)", language="en"
)


@medicines.route("/api/medicines", methods=["GET"])
@login_required
def api_medicines():
    """
    Name:       api_medicines()
    Purpose:    Fetches all the medicines associated with the current user, along with their related
                reminders. It returns the data in JSON format to be consumed by an API or client-side
                application.
    Parameters: None
    Returns:    JSON: A JSON response containing the user's medicines and their respective reminders,
                    including reminder times and statuses.
    """

    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []

    # Fetch associated medicine names and reminders for each user_medicine entry
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)

        # Fetch reminders for this user_medicine
        reminders = MedicationReminder.query.filter_by(
            user_medicine_id=user_medicine.id
        ).all()

        # Add reminder details to the medicine data
        reminder_data = []
        for reminder in reminders:
            reminder_data.append(
                {"reminder_time": reminder.reminder_time, "status": reminder.status}
            )

        medicines.append(
            {
                "id": medicine.id,
                "name": medicine.name,
                "dosage": user_medicine.dosage,
                "frequency": user_medicine.frequency,
                "notes": user_medicine.notes,
                "reminders": reminder_data,  # Include reminder data here
            }
        )

    return jsonify(medicines)


@medicines.route("/add_medicine", methods=["GET", "POST"])
@login_required
def add_medicine():
    """
    Name:       add_medicine()
    Purpose:    Handles the process of adding a new medicine to the user's medication list, including
                any reminders. It validates the form data, creates or updates the medicine and reminder
                records in the database, and provides feedback to the user.
    Parameters: None
    Returns:    Rendered Template: A template for adding medicine (`add_medicine.html`) if the form
                is not submitted or contains errors. Redirects to the 'my_medicine' page if the
                medicine and reminder are successfully added.
    """

    medicine_form = MedicineForm()
    reminder_form = ReminderForm()

    if request.method == "POST":
        # Loop through dynamically generated reminder fields
        reminder_count = get_reminder_count(medicine_form.frequency.data)
        for i in range(reminder_count):
            reminder_time = request.form.get(f"reminder_time_{i}")
            reminder_message = request.form.get(f"reminder_message_{i}")
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
            notes=notes,
        )
        db.session.add(user_medicine)
        db.session.commit()

        # Create a reminder if reminder details are provided
        reminder_count = get_reminder_count(frequency)
        for i in range(reminder_count):
            reminder_time = request.form.get(f"reminder_time_{i}")
            reminder_message = request.form.get(f"reminder_message_{i}")
            status = reminder_form.status.data

            if reminder_time and reminder_message:
                reminder = MedicationReminder(
                    user_id=current_user.id,
                    user_medicine_id=user_medicine.id,
                    reminder_time=reminder_time,
                    reminder_message=reminder_message,
                    status=status,
                )
                db.session.add(reminder)

        try:
            db.session.commit()
            flash("Medicine and reminder added successfully!", "success")
            return redirect(url_for("medicines.my_medicine"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")

    return render_template(
        "add_medicine.html", medicine_form=medicine_form, reminder_form=reminder_form
    )


def get_reminder_count(frequency):
    """
    Name:       get_reminder_count()
    Purpose:    Determines the number of reminders based on the frequency of the medication.
                It maps medication frequency to the number of reminders that should be set.
    Parameters: frequency (str): The frequency of the medication (e.g., 'Once a Day', 'Twice a Day').
    Returns:    int: The number of reminders based on the frequency.
                Returns 0 if the frequency does not match any predefined options.
    """

    if frequency == "Once a Day":
        return 1
    elif frequency == "Twice a Day":
        return 2
    elif frequency == "Three Times a Day":
        return 3
    elif frequency == "Four Times a Day":
        return 4
    return 0  # Default to 0 if no frequency is matched


# Route for viewing the user's medicines
@medicines.route("/my_medicine")
@login_required
def my_medicine():
    """
    Name:       my_medicine()
    Purpose:    Retrieves and displays the user's medicines, including associated dosage, frequency,
                and reminders. It sorts the medicines by the first reminder time and groups them accordingly.
    Parameters: None
    Returns:    Response: The rendered HTML template displaying the user's medicines and associated details.
    """

    # Query medicines associated with the current user
    user_medicines = UserMedicine.query.filter_by(user_id=current_user.id).all()
    medicines = []

    # Fetch associated medicine names and reminders for each user_medicine entry
    for user_medicine in user_medicines:
        medicine = Medicine.query.get(user_medicine.medicine_id)

        # Fetch reminders for this user_medicine
        reminders = MedicationReminder.query.filter_by(
            user_medicine_id=user_medicine.id
        ).all()

        # Format reminder data for template
        reminder_data = []
        for reminder in reminders:
            reminder_data.append(
                {"reminder_time": reminder.reminder_time, "status": reminder.status}
            )

        medicines.append(
            {
                "id": medicine.id,
                "name": medicine.name,
                "dosage": user_medicine.dosage,
                "frequency": user_medicine.frequency,
                "notes": user_medicine.notes,
                "reminders": reminder_data,  # Add reminders to the template data
            }
        )

    # Sort medicines by the first reminder time, then by medicine name
    medicines.sort(
        key=lambda x: (
            (
                x["reminders"][0]["reminder_time"] if x["reminders"] else time.min
            ),  # Use time.min for empty reminders
            x["name"],
        )
    )

    return render_template(
        "my_medicine.html", medicines=medicines, page_class="my_medicine_page"
    )


@medicines.route("/delete_medicine/<int:medicine_id>", methods=["POST"])
@login_required
def delete_medicine(medicine_id):
    """
    Name:       delete_medicine(medicine_id)
    Purpose:    Deletes a specific medicine from the user's medicine list, including all associated reminders.
                The function verifies the medicine's existence for the logged-in user before performing deletion.
    Parameters: medicine_id (int): The ID of the medicine to be deleted.
    Returns:    Response: Redirects to the 'my_medicine' page after successfully deleting the medicine,
                or flashes an error message if the medicine is not found.
    """

    # Find the record from the user_medicines table
    user_medicine = UserMedicine.query.filter_by(
        medicine_id=medicine_id, user_id=current_user.id
    ).first()

    if user_medicine is not None:
        # Delete associated reminders for the medicine
        MedicationReminder.query.filter_by(user_medicine_id=user_medicine.id).delete()

        # Delete the user_medicine record
        db.session.delete(user_medicine)
        db.session.commit()
        flash("Medicine deleted successfully!", "success")
        return redirect(url_for("medicines.my_medicine"))
    else:
        flash("Medicine not found.", "danger")
        return redirect(url_for("medicines.my_medicine"))


@medicines.route("/edit_medicine/<int:medicine_id>", methods=["GET", "POST"])
@login_required
def edit_medicine(medicine_id):
    """
    Name:       edit_medicine(medicine_id)
    Purpose:    Allows a user to edit the details of an existing medicine, including dosage, frequency,
                notes, and reminders. The function pre-fills the form with current data and updates
                the database after form submission.
    Parameters: medicine_id (int): The ID of the medicine to be edited.
    Returns:    Response: Renders the 'edit_medicine.html' template with the form for editing,
                or redirects to 'my_medicine' page after successfully saving the changes,
                or flashes an error message if the update fails.
    """

    # Retrieve the medicine and user_medicine from the database
    medicine = Medicine.query.get_or_404(medicine_id)
    user_medicine = UserMedicine.query.filter_by(
        medicine_id=medicine_id, user_id=current_user.id
    ).first_or_404()

    # Create the form
    form = EditMedicineForm()

    # Handle GET request to pre-fill the form with current data
    if request.method == "GET":
        form.name.data = medicine.name
        form.dosage.data = user_medicine.dosage
        form.frequency.data = user_medicine.frequency
        form.notes.data = user_medicine.notes

        # Prepare reminder data for JavaScript
        reminder_data = []
        if user_medicine.reminders:
            for reminder in user_medicine.reminders:
                reminder_data.append(
                    {
                        "reminder_time": (
                            reminder.reminder_time.strftime("%H:%M")
                            if reminder.reminder_time
                            else ""
                        ),
                        "reminder_message": reminder.reminder_message or "",
                        "status": reminder.status or "pending",
                    }
                )

        return render_template(
            "edit_medicine.html",
            form=form,
            medicine=medicine,
            user_medicine=user_medicine,
            reminder_data=reminder_data,
        )

    # Handle POST request for form submission
    if request.method == "POST":
        # Extract reminder data from the form dynamically based on the number of reminders
        reminder_times = [
            request.form.get(f"reminder_time_{i}") for i in range(4)
        ]  # Max 4 reminders
        reminder_messages = [
            request.form.get(f"reminder_message_{i}") for i in range(4)
        ]
        statuses = [request.form.get(f"status_{i}") for i in range(4)]

        # Manually validate statuses
        valid_status_choices = ["pending", "sent"]
        statuses = [
            status if status in valid_status_choices else "pending"
            for status in statuses
        ]

        # Filter out empty reminder data
        filtered_reminders = [
            (time, message, status)
            for time, message, status in zip(
                reminder_times, reminder_messages, statuses
            )
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
            for i, (reminder_time, reminder_message, status) in enumerate(
                filtered_reminders
            ):
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
                        user_medicine_id=user_medicine.id,
                        user_id=current_user.id,
                    )
                    db.session.add(new_reminder)

            # Commit changes to the database
            try:
                db.session.commit()
                flash("Changes saved successfully!", "success")
                return redirect(url_for("medicines.my_medicine"))
            except Exception as e:
                db.session.rollback()
                flash("Update failed. Please try again.", "error")
                print(f"Error: {e}")
        else:
            flash("Form validation failed", "error")
            print("Form validation failed. Errors:", form.errors)

    return render_template(
        "edit_medicine.html",
        form=form,
        medicine=medicine,
        user_medicine=user_medicine,
        reminder_data=[],
    )


@medicines.route("/medicine/<int:medicine_id>", methods=["GET"])
@login_required
def medicine_details(medicine_id):
    """
    Name:       medicine_details(medicine_id)
    Purpose:    Displays detailed information about a specific medicine, including data fetched from
                Wikipedia. If the Wikipedia page exists, the sections are displayed; otherwise, an
                error message is shown.
    Parameters: medicine_id (int): The ID of the medicine whose details are to be retrieved.
    Returns:    Response: Renders the 'medicine_details.html' template with the medicine details and
                Wikipedia sections, or a message indicating that the Wikipedia page was not found.
    """

    # Query the medicine from the database
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return "Medicine not found", 404

    # Use wikipedia-api to search for the medicine
    page = wiki_wiki.page(medicine.name)

    # Check if the page exists
    if not page.exists():
        return render_template(
            "medicine_details.html", medicine=medicine, wiki_not_found=True
        )

    # Get the sections from the Wikipedia page
    sections = []
    for section in page.sections:
        sections.append(
            {
                "title": section.title,
                "content": section.text[
                    :500
                ],  # Just show the first 500 characters initially
                "full_content": section.text,  # The full content for later expansion
            }
        )

    return render_template(
        "medicine_details.html", medicine=medicine, sections=sections
    )
