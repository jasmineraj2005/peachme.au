# Use an official Python image as the base
FROM python:3.10-slim

# Install system dependencies
RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first to speed up caching
COPY requirements.txt .


# Install Python dependencies
RUN pip install --no-cache-dir openai-whisper torch ffmpeg-python

# Copy rest of the files
COPY . .

# Command to run the script (can be changed later)
CMD ["python", "main.py"]
