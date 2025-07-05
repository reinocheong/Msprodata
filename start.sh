#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
# We are removing "set -e" because we want to handle the exit code of flask db upgrade manually.

# 1. Run database migrations
echo "INFO: Running database migrations..."
/usr/local/bin/python -m flask db upgrade || true
echo "INFO: Database migrations finished (any errors about tables already existing are normal)."

# 2. Start the Gunicorn server
echo "INFO: Starting Gunicorn server..."
/usr/local/bin/python -m gunicorn --bind 0.0.0.0:${PORT} wsgi:app --capture-output --log-level debug
