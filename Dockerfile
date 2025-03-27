FROM python:3.11-slim

# Install system dependencies including ffmpeg and build tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies in one layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip/*

# Copy the application code
COPY main.py .
COPY app ./app


# Create necessary directories
RUN mkdir -p media

# Expose the port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"] 