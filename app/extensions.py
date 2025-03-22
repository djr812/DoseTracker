"""
extensions.py
-------------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/app/extensions.py

Purpose:    Initializes and configures third-party extensions (e.g., SQLAlchemy, Bcrypt) 
            for use within the Flask application.
"""


from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()