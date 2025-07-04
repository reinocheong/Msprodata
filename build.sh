#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Python dependencies
echo "----> Installing Python dependencies..."
pip install -r requirements.txt

# 2. Install wkhtmltopdf into a local directory
echo "----> Installing wkhtmltopdf..."

# Create a 'bin' directory in our project's root
# This is a writable directory we control
BIN_DIR=${RENDER_ROOT}/bin
mkdir -p ${BIN_DIR}

WKHTMLTOPDF_VERSION="0.12.6-1"
WKHTMLTOPDF_URL="https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}.buster_amd64.deb"

# Download the package
wget -q -O wkhtmltox.deb ${WKHTMLTOPDF_URL}

# Create a temporary directory to extract the contents
EXTRACT_DIR=/tmp/wkhtmltox
mkdir -p ${EXTRACT_DIR}
# Extract the .deb file
dpkg -x wkhtmltox.deb ${EXTRACT_DIR}

# Copy the executables to our local 'bin' directory
cp ${EXTRACT_DIR}/usr/local/bin/wkhtmltopdf ${BIN_DIR}/
cp ${EXTRACT_DIR}/usr/local/bin/wkhtmltoimage ${BIN_DIR}/

# Add our local 'bin' directory to the PATH for this build script
export PATH="${BIN_DIR}:${PATH}"

# Verify the installation by checking the version
# The system will now find it in our local bin directory
echo "----> Verifying wkhtmltopdf installation..."
wkhtmltopdf --version

# Clean up downloaded and extracted files
rm wkhtmltox.deb
rm -rf ${EXTRACT_DIR}

echo "----> Build script finished successfully."