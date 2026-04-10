from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading
import shutil
import re

app = Flask(__name__)

# Render's temporary storage
DOWNLOAD_FOLDER = '/tmp/youtube'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Standard FFmpeg path in Docker
MY_FFMPEG_PATH = '/usr/bin/ffmpeg'

def clean_filename(title):
    # Removes characters that break iPhone file saving
    return re.sub(r'[^\w\- ]', '', title).strip()

@app.route('/')
def home():
    return "YouTube MP3 Service is Live"

@app.route('/download')
def download_mp3():
    url = request.args.get('url')
    if not url:
        return "Error: No URL provided", 400

    file_id = str(int(time.time()))
    
ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        
        # THIS IS THE KEY LINE
        'cookiefile': 'cookies.txt', 
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'audio')
            safe_title = clean_filename(original_title)
            final_path = f"{DOWNLOAD_FOLDER}/{file_id}.mp3"

        if not os.path.exists(final_path):
            return "Error: MP3 conversion failed", 500

        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(60) # Wait 1 min to ensure download completes
                if os.path.exists(final_path):
                    os.remove(final_path)
            threading.Thread(target=delete_later).start()
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=f"{safe_title}.mp3",
            mimetype='audio/mpeg'
        )
        
    except Exception as e:
        print(f"Server Error: {e}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
