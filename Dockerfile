# Dockerfile for Ollama-based Alt Text Generator API
# Uses Python 3.12 slim image for minimal size while maintaining compatibility
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install Python dependencies
# Copy requirements first for better Docker layer caching
COPY requirements.txt .
# Install dependencies without caching pip packages to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into container
COPY server.py .

# Environment variables
# PYTHONUNBUFFERED ensures Python output is sent directly to stdout/stderr
# This is important for Docker logs to show real-time output
ENV PYTHONUNBUFFERED=1

# Expose port 5000 for the Flask/Gunicorn server
EXPOSE 5000

# Start Gunicorn WSGI server
# - server:app: refers to the Flask app instance in server.py
# - --bind 0.0.0.0:5000: listen on all interfaces on port 5000
# - --timeout 0: no timeout (useful for long-running image processing requests)
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:5000", "--timeout", "0"]