from flask import Flask
from extensions import db, login_manager
from flask_migrate import Migrate
import os

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_development')
    
    # Configure database URI
    database_url = "postgresql://msprodata_db_8gfs_user:lFhaCP6EWDZ87DcRojEUVxANJ9AInJrQ@dpg-d1k9e9ur433s73c9d1ig-a.singapore-postgres.render.com/msprodata_db_8gfs"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Register the seed-data command
    from commands import seed_data_command
    app.cli.add_command(seed_data_command)

    # Import and register blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Define the user loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    return app
