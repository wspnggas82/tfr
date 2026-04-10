# Use Python image
FROM python:3.10-slim

# Install FFmpeg and system tools
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
