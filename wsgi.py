import os
from app import create_app

print("WSGI: Starting application entrypoint...")

# Create the Flask app instance
print("WSGI: Calling create_app()...")
app = create_app()
print("WSGI: create_app() returned successfully.")

if __name__ == "__main__":
    # This block is for local development, not for production with Gunicorn
    print("WSGI: Running in local development mode.")
    app.run(debug=True)