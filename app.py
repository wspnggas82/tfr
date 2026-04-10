from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading
import shutil

app = Flask(__name__)

# Render uses /tmp for writing files
DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# In Docker, FFmpeg is always here:
MY_FFMPEG_PATH = '/usr/bin/ffmpeg'

@app.route('/')
def home():
    return "Server is LIVE"

@app.route('/download')
def download_audio():
    url = request.args.get('url')
    if not url:
        return "Error: No URL provided", 400

    # Use a timestamp to keep the filename simple and avoid errors
    file_id = str(int(time.time()))

    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': MY_FFMPEG_PATH,
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        # THE FIX: This tricks YouTube into thinking you're on a real device
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Render needs to know the exact title for the download name
            original_title = info.get('title', 'audio')
            final_filename = f"{DOWNLOAD_FOLDER}/{file_id}.mp3"

        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(60) # Keep it for 1 minute so the download finishes
                if os.path.exists(final_filename):
                    os.remove(final_filename)
            threading.Thread(target=delete_later).start()
            return response

        return send_file(
            final_filename, 
            as_attachment=True, 
            download_name=f"{original_title}.mp3"
        )
        
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Use Render's dynamic port
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
