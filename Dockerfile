# Use the Debian bookworm-based slim image
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ------------------------------------------------------------
# Configure Liara Debian Mirror (for bookworm)
# ------------------------------------------------------------
RUN echo "deb https://linux-mirror.liara.ir/repository/debian bookworm main non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://linux-mirror.liara.ir/repository/debian-security bookworm-security main non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://linux-mirror.liara.ir/repository/debian bookworm-updates main non-free-firmware" >> /etc/apt/sources.list

# Install system dependencies (now they will install correctly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Configure Liara PyPI Mirror
# ------------------------------------------------------------
ENV PIP_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput --settings=bookstore_backend.settings.production

EXPOSE 8000

# Use a robust Gunicorn command (preload, longer timeout)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers=2", "--threads=2", "--timeout=120", "--preload", "bookstore_backend.wsgi:application"]