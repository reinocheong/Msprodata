#!/bin/sh
set -e
python -m gunicorn wsgi:app