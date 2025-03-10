from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Initialize the database object
db = SQLAlchemy()

def create_app():
    # Create the Flask app
    app = Flask(__name__)

    # Load environment variables from the .env file
    load_dotenv()

    # Configure the app from the Config class
    app.config.from_object('config.Config')

    # Initialize the database with the app
    db.init_app(app)

    # Example route to test connection
    @app.route('/')
    def index():
        try:
            # Test if the database connection works
            with app.app_context():
                db.create_all()  # This is optional, used to create tables if not existing
            return "Database connection successful!"
        except Exception as e:
            return f"Error connecting to the database: {str(e)}"

    return app
