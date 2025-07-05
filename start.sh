#!/bin/sh
set -e
/usr/local/bin/gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 300 --workers 2 --worker-class gevent --access-logfile - --error-logfile - wsgi:app
