#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Python dependencies
echo "----> Installing Python dependencies..."
pip install -r requirements.txt

# 2. Install wkhtmltopdf from pre-compiled binary (the most reliable method)
echo "----> Installing wkhtmltopdf..."
WKHTMLTOPDF_VERSION="0.12.6-1"
# We use the 'buster' version as it's a common Debian base for build environments
WKHTMLTOPDF_URL="https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}.buster_amd64.deb"

# Download the package
wget -q -O wkhtmltox.deb ${WKHTMLTOPDF_URL}

# Create a directory to extract the contents
mkdir -p /tmp/wkhtmltox
# Extract the .deb file
dpkg -x wkhtmltox.deb /tmp/wkhtmltox

# Copy the executable to a location in the system's PATH
# This makes 'wkhtmltopdf' command available globally
cp /tmp/wkhtmltox/usr/local/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
cp /tmp/wkhtmltox/usr/local/bin/wkhtmltoimage /usr/local/bin/wkhtmltoimage

# Verify the installation
echo "----> Verifying wkhtmltopdf installation..."
wkhtmltopdf --version

# Clean up downloaded and extracted files
rm wkhtmltox.deb
rm -rf /tmp/wkhtmltox

echo "----> Build script finished successfully."
