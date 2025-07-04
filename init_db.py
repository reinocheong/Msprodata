
import os
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from app import create_app, db

# Set a dummy database URL to allow the app to initialize
os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost/db'

# Create an app instance for the migration context
app = create_app()

def run_migrations():
    with app.app_context():
        # Equivalent of 'flask db init'
        if not os.path.exists('migrations'):
            init()
            print("Initialized migrations directory.")
        
        # Equivalent of 'flask db migrate'
        # We run this in "offline" mode by not connecting to a database
        # It will generate the script based on the models
        migrate(message="Initial migration.", autogenerate=False, sql=True)
        print("Generated initial migration script.")
        
        # We don't run upgrade locally, it will be run on the server
        # upgrade()
        print("Skipping database upgrade on local machine.")

if __name__ == '__main__':
    run_migrations()
