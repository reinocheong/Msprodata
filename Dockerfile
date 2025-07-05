# Stage 1: Build stage with system dependencies
FROM python:3.11-slim as builder

# Install system dependencies required for WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-cffi \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements.txt


# Stage 2: Final stage
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for WeasyPrint (runtime)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy the rest of the application code
COPY app.py .
COPY auth.py .
COPY config.py .
COPY extensions.py .
COPY models.py .
COPY routes.py .
COPY utils.py .
COPY wsgi.py .
COPY alembic.ini .
COPY requirements.txt .
COPY migrations/ ./migrations/
COPY static/ ./static/
COPY templates/ ./templates/

ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# Set the entrypoint for the application