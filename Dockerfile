FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# This line copies EVERYTHING (including cookies.txt) into the server
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "youtube:app"]
