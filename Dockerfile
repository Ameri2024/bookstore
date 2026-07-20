# Use the official Python slim image for a smaller footprint
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies required for PostgreSQL, Pillow, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Collect static files (optional – you can also run this at startup)
RUN python manage.py collectstatic --noinput --settings=bookstore_backend.settings.production

# Expose the port Gunicorn will listen on
EXPOSE 8000

# Start Gunicorn with the production settings
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "bookstore_backend.wsgi:application"]