FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY generator/ ./generator/
COPY backup/ ./backup/
COPY validation/ ./validation/
COPY config/ ./config/
COPY main.py .

# Create directories
RUN mkdir -p /app/backup_data /app/logs

# Default command (overridden in docker-compose)
CMD ["python", "main.py"]
