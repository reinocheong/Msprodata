#!/usr/bin/env bash
# exit on error
set -o errexit

echo "----> Build script started."

# 0. Install essential build tools
# Render's base image is minimal, so we need to install tools like wget and dpkg.
echo "----> Step 0: Installing essential build tools (wget, dpkg)..."
apt-get update -y
apt-get install -y wget dpkg
echo "----> Step 0: Essential tools installed."

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

# Download the package
echo "----> Step 2a: Downloading wkhtmltopdf from ${WKHTMLTOPDF_URL}..."
wget -q -O ${DEB_FILE} ${WKHTMLTOPDF_URL}
echo "----> Step 2a: Download successful."

# Extract the package
echo "----> Step 2b: Extracting ${DEB_FILE}..."
mkdir -p ${EXTRACT_DIR}
dpkg -x ${DEB_FILE} ${EXTRACT_DIR}
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
echo "----> Step 3: Verification step finished."

# Clean up
echo "----> Step 4: Cleaning up temporary files..."
rm ${DEB_FILE}
rm -rf ${EXTRACT_DIR}
echo "----> Step 4: Cleanup successful."

echo "----> Build script finished."