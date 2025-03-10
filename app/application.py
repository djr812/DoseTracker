from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Set the login_view to point to your login route
login_manager.login_view = 'auth.login'

def create_app():
    # Initialize the Flask app
    app = Flask(__name__)

    # App configuration
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import models and routes after extensions are initialized
    with app.app_context():
        from .models import User  
        from .auth.routes import auth_bp  
        from .main.routes import main_bp

    @login_manager.user_loader
    def load_user(user_id):
        # This function loads the user from the database
        return User.query.get(int(user_id))

    # Register Blueprints 
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)  

    return app


