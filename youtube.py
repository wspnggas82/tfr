from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading
import re

app = Flask(__name__)

# Render's temporary storage
DOWNLOAD_FOLDER = '/tmp/youtube'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

MY_FFMPEG_PATH = '/usr/bin/ffmpeg'

def clean_filename(title):
    return re.sub(r'[^\w\- ]', '', title).strip()

@app.route('/')
def home():
    return "YouTube Service is Live"

@app.route('/download')
def download_mp3():
    url = request.args.get('url')
    if not url:
        return "Error: No URL provided", 400

    file_id = str(int(time.time()))
    final_path = f"{DOWNLOAD_FOLDER}/{file_id}.mp3"
    
  ydl_opts = {
        # This tells it: "Get the best audio, but if that fails, get whatever audio is there"
        'format': 'bestaudio/best',
        'ffmpeg_location': MY_FFMPEG_PATH,
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies.txt', 
        # Added these two lines to be more compatible with different videos
        'ignoreerrors': True,
        'preferredquality': '192',
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web'],
            }
        },
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {'key': 'FFmpegMetadata'},
            {'key': 'EmbedThumbnail'},
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'audio')
            safe_title = clean_filename(original_title)

        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(60)
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
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
