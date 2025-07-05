#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# 1. Run database migrations
echo "INFO: Running database migrations..."
/usr/local/bin/python -m flask db upgrade
echo "INFO: Database migrations complete."

# 2. Start the Gunicorn server
echo "INFO: Starting Gunicorn server..."
/usr/local/bin/python -m gunicorn --bind 0.0.0.0:${PORT} wsgi:app --capture-output --log-level debug
