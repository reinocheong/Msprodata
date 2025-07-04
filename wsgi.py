from app import create_app

# Create an application instance by calling the factory function
app = create_app()

# This block allows running the app directly with `python wsgi.py` for local development.
# Gunicorn and other production WSGI servers will not use this block.
if __name__ == "__main__":
    # Note: `debug=True` is not recommended for production.
    # The production server (Gunicorn) will handle the host and port.
    app.run(debug=True)
