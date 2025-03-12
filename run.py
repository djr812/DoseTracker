from app.application import create_app

# Create the Flask app
app = create_app()

application=app

if __name__ == '__main__':
    app.run(debug=True)
