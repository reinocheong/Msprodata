from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

print("APP.PY: Top-level, script is being parsed.")

# Initialize extensions
print("APP.PY: Initializing extensions (db, login_manager).")
db = SQLAlchemy()
login_manager = LoginManager()
print("APP.PY: Extensions initialized.")

def create_app():
    """Create and configure an instance of the Flask application."""
    print("CREATE_APP: Starting factory function.")
    
    app = Flask(__name__)
    print("CREATE_APP: Flask app instance created.")

    # Configure the app
    # Use a real secret key in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_development')
    print(f"CREATE_APP: SECRET_KEY configured.")

    # Configure database URI
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("CREATE_APP: FATAL - DATABASE_URL environment variable not set!")
        raise ValueError("No DATABASE_URL set for the application")
    
    # Heroku/Render uses 'postgres://', but SQLAlchemy prefers 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print(f"CREATE_APP: Database URI configured: {database_url[:30]}...") # Log only a prefix for security

    # Initialize extensions with the app
    print("CREATE_APP: Initializing db with app...")
    db.init_app(app)
    print("CREATE_APP: db initialized.")

    print("CREATE_APP: Initializing login_manager with app...")
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    print("CREATE_APP: login_manager initialized.")

    # Import and register blueprints
    print("CREATE_APP: Importing blueprints...")
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    print("CREATE_APP: Main blueprint registered.")

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    print("CREATE_APP: Auth blueprint registered.")

    # Define the user loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        print(f"LOAD_USER: Loading user with ID: {user_id}")
        from .models import User
        # Use with_pk() for primary key lookup which is more efficient
        return User.query.get(int(user_id))

    print("CREATE_APP: Factory function finished. Returning app.")
    return app