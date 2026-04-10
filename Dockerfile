FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This 'CMD' is a backup. We will override this in Render settings.
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "youtube:app"]
