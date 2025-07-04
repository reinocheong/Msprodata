from flask import Flask

# This is a minimal Flask app for testing the deployment process itself.
# It helps verify that the Docker container, Gunicorn, and Render's routing are all working correctly.
# If this deploys successfully, the problem lies within the create_app() function in app.py.

app = Flask(__name__)

@app.route('/')
def health_check():
    """
    A simple health check endpoint that Render can hit to confirm the service is up.
    """
    return "Minimal test app is running correctly!", 200

# --- The original code is temporarily commented out for the test ---
# from app import create_app
# app = create_app()
# if __name__ == "__main__":
#     app.run(debug=True)