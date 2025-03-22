"""
run.py
------

Author:     David Rogers
Email:      dave@djrogers.net.au
Path:       /path/to/project/run.py

Purpose:    Starts the Flask application and runs the development server.
"""

from app.application import create_app

# Create the Flask app
app = create_app()

application=app

if __name__ == '__main__':
    app.run(debug=False)
