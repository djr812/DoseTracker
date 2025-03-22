# DoseTracker
A web-based Medicine Dose tracker for the forgetful.

## Overview

The **Dose Tracker** is a web application built with Flask that helps users manage their medication schedules. It allows users to track their medicines, set reminders, and receive notifications about their medication timings. The app uses **Flask** for the backend, **SQLAlchemy** for database management, and **Flask-Mail** to send PDF reports to users.

## Features

- **User Authentication:** Sign up, login, and logout functionality using Flask-Login.
- **Medicine Management:** Add, edit, delete, and view medicines along with their dosage, frequency, and notes.
- **Medication Reminders:** Set reminders for each medicine at specified times and send SMS reminders.
- **PDF Reports:** Generate and send PDF reports via email containing a list of the user's medicines and reminders.
- **API Access:** Access the user's medicines and reminders via an API endpoint.

## Technologies Used

- **Flask**: The web framework for building the application.
- **SQLAlchemy**: ORM for database management.
- **Flask-Login**: Manages user sessions and authentication.
- **Flask-Mail**: Sends emails, including PDF attachments.
- **APScheduler**: Schedule SMS delivery of medication dose reminders.
- **wtforms**: Manages form generation and validation.
- **Wikipedia-API**: Retrieves Wikipedia data for medicines.

## Requirements

- Python 3.x
- Flask
- Flask-Login
- Flask-Mail
- Flask-SQLAlchemy
- Flask-Bcrypt
- Wikipedia-API
- wtforms
- APScheduler (optional for scheduled tasks)
- Twilio (optional for sending SMS reminders)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/DoseTracker.git
    cd DoseTracker
    ```

2. Set up a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set environment variables for your Flask app (example):

    ```bash
    export FLASK_APP=app
    export FLASK_ENV=development
    export SECRET_KEY=your_secret_key
    export MAIL_USERNAME=your_email@example.com
    export MAIL_PASSWORD=your_email_password
    ```

5. Create the database and run the application:

    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    flask run
    ```

## File Structure

/dose-tracker /app /auth - routes.py 
### Authentication-related routes (login, logout, sign-up) 

/main - routes.py 
### Main application routes (medicine management, API) 

/medicines - routes.py 
### Medicine management routes (add, delete, edit, details) 

/templates - index.html 
### Main landing page template 

- sign_up.html 
### Sign up page template 

- add_medicine.html 
### Add medicine page template 

/static /css - style.css 
### Custom CSS styles for the app 

/js - app.js 
### JavaScript for interactive features 

/models - models.py 
### Database models for User, Medicine, etc. 

/forms - forms.py 
### Forms for user input (login, sign-up, medicine forms) 

/application.py 
### Initializes Flask app, sets up extensions (SQLAlchemy, Mail) 

/migrations - (Database migrations) 

/requirements.txt 
### Required Python packages 

- README.md 
### Project documentation


## How to Use

1. **User Authentication:**
    - Users can sign up, log in, and log out to track their medications securely.
    
2. **Medicine Management:**
    - Users can add new medicines, set reminders, and edit or delete existing medicines.
    
3. **Reminder System:**
    - Users can set reminders for when to take their medicine, with the option to choose multiple reminders per day.
    
4. **Viewing Medicines:**
    - Users can view a list of all their medicines, including reminder times.

5. **PDF Reports:**
    - Users can generate and receive PDF reports of their medicines, including reminder times.

## Routes

### Authentication Routes (Auth)

- **`/login`**: User login page.
- **`/logout`**: Log out the user and end their session.
- **`/sign-up`**: Sign-up page for new users.
- **`/forgot_password`**: Password recovery page.
- **`/reset_password/<token>`**: Reset the user’s password using a secure token.
- **`/user-admin`**: User profile management page.

### Medicine Routes (Medicines)

- **`/add_medicine`**: Page to add a new medicine to the user’s list.
- **`/my_medicine`**: View all medicines added by the user along with reminders.
- **`/edit_medicine/<medicine_id>`**: Edit a specific medicine’s details and reminders.
- **`/delete_medicine/<medicine_id>`**: Delete a medicine from the user’s list.
- **`/medicine/<medicine_id>`**: View detailed information about a specific medicine, including Wikipedia content.

### API Routes (Medicines)

- **`/api/medicines`**: An API endpoint to retrieve the user’s medicines and their associated reminders in JSON format.

## Form Validation

- **LoginForm**: Validates user login credentials.
- **SignUpForm**: Validates user sign-up details (email, password, etc.).
- **MedicineForm**: Validates medicine addition details (name, dosage, etc.).
- **ReminderForm**: Validates reminder times and messages.
- **EditMedicineForm**: Validates updates to existing medicines.

## Error Handling

The application includes custom error handling for common issues such as:
- Invalid credentials during login
- Invalid or expired reset tokens for password recovery
- Errors during database operations (e.g., committing new records)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> **Note:** Be sure to update any credentials, API keys, or sensitive information before deploying the application to production.
