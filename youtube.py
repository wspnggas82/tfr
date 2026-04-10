from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading
import re

app = Flask(__name__)

# Use /tmp for Render compatibility
DOWNLOAD_FOLDER = '/tmp/youtube'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return "YouTube Service is Live"

@app.route('/download')
def download_mp3():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    file_id = str(int(time.time()))
    # Simplified options to ensure it boots
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'noplaylist': True,
        'cookiefile': 'cookies.txt', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            final_path = f"{DOWNLOAD_FOLDER}/{file_id}.mp3"

        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(60)
                if os.path.exists(final_path):
                    os.remove(final_path)
            threading.Thread(target=delete_later).start()
            return response

        return send_file(final_path, as_attachment=True, download_name="audio.mp3")
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Render default port
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
