FROM python:3.10-slim

# Install FFmpeg AND Node.js (this is the JS runtime YouTube wants)
RUN apt-get update && apt-get install -y ffmpeg nodejs && apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "youtube:app"]
