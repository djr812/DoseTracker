from app import create_app

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Run the app with debugging enabled
    app.run(debug=True)
