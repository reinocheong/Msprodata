#!/bin/sh
/usr/local/bin/python -m gunicorn --bind 0.0.0.0:${PORT} wsgi:app --capture-output --log-level debug
