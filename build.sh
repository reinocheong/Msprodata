#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Install weasyprint system dependencies
apt-get update && apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1
