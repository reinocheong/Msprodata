# Step 1: Use an official Python runtime as a parent image
# We use python:3.11-slim-buster which is a lightweight Debian-based image
FROM python:3.11-slim-buster

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Install wkhtmltopdf and its dependencies
# We run apt-get update first, and then install the required libraries and wkhtmltopdf itself.
# This is the most reliable way to install system packages in Docker.
RUN apt-get update && \
    apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libfontconfig1 \
    libxext6 && \
    # Clean up the apt-get cache to keep the image small
    rm -rf /var/lib/apt/lists/*

# Step 4: Copy the requirements file into the container
COPY requirements.txt .

# Step 5: Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the rest of your application's code into the container
COPY . .

# Step 7: Expose the port your app runs on
# The $PORT environment variable will be supplied by Render.
# We default to 10000 if it's not set.
EXPOSE 10000

# Step 8: Define the command to run your app
# This will be executed when the container starts.
# We use gunicorn to run the Flask app.
CMD gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT app:app
