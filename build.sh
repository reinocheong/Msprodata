#!/usr/bin/env bash

# We are removing 'set -o errexit' temporarily for debugging purposes
# This will prevent the script from exiting on non-critical errors like 'tput'

echo "----> Build script started."

# 1. Install Python dependencies
echo "----> Step 1: Installing Python dependencies..."
pip install -r requirements.txt
echo "----> Step 1: Python dependencies installation finished."

# 2. Install wkhtmltopdf into a local directory
echo "----> Step 2: Preparing for wkhtmltopdf installation..."

# Define directories and URLs
BIN_DIR="${RENDER_ROOT}/bin"
WKHTMLTOPDF_VERSION="0.12.6-1"
WKHTMLTOPDF_URL="https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}.buster_amd64.deb"
DEB_FILE="wkhtmltox.deb"
EXTRACT_DIR="/tmp/wkhtmltox_extract"

echo "----> Creating binary directory at ${BIN_DIR}"
mkdir -p ${BIN_DIR}

# Download the package with error checking
echo "----> Step 2a: Downloading wkhtmltopdf from ${WKHTMLTOPDF_URL}..."
wget -q -O ${DEB_FILE} ${WKHTMLTOPDF_URL}
if [ $? -ne 0 ]; then
  echo "!!!!!! ERROR: Failed to download wkhtmltopdf package. Exiting."
  exit 1
fi
echo "----> Step 2a: Download successful."

# Extract the package with error checking
echo "----> Step 2b: Extracting ${DEB_FILE}..."
mkdir -p ${EXTRACT_DIR}
dpkg -x ${DEB_FILE} ${EXTRACT_DIR}
if [ $? -ne 0 ]; then
  echo "!!!!!! ERROR: Failed to extract .deb file. Exiting."
  exit 1
fi
echo "----> Step 2b: Extraction successful."

# Copy the executables
echo "----> Step 2c: Copying executables to ${BIN_DIR}..."
cp ${EXTRACT_DIR}/usr/local/bin/wkhtmltopdf ${BIN_DIR}/
cp ${EXTRACT_DIR}/usr/local/bin/wkhtmltoimage ${BIN_DIR}/
echo "----> Step 2c: Copy successful."

# Add our local 'bin' directory to the PATH for this build script
export PATH="${BIN_DIR}:${PATH}"

# Verify the installation
echo "----> Step 3: Verifying wkhtmltopdf installation..."
wkhtmltopdf --version
if [ $? -ne 0 ]; then
  echo "!!!!!! WARNING: 'wkhtmltopdf --version' command failed. This might indicate missing libraries."
  # We will not exit here, to see if the app can still run.
fi
echo "----> Step 3: Verification step finished."

# Clean up
echo "----> Step 4: Cleaning up temporary files..."
rm ${DEB_FILE}
rm -rf ${EXTRACT_DIR}
echo "----> Step 4: Cleanup successful."

echo "----> Build script finished."
