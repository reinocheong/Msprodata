#!/usr/bin/env bash
# Exit on error
set -o errexit

# Run database migrations
flask db upgrade
