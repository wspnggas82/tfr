from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading
import shutil
import re

app = Flask(__name__)

# Render requires using /tmp for any file writing
DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Docker will install ffmpeg to the standard path
MY_FFMPEG_PATH = "/usr/bin/ffmpeg"

def clean_filename(title):
    # Removes special characters that confuse the iPhone file system
    return re.sub(r'[^\w\- ]', '', title).strip()

@app.route('/')
def home():
    return "Downloader is Online (Docker Version)"

@app.route('/download')
def master_download():
    url = request.args.get('url')
    if not url:
        return "Error: No URL provided", 400

    print(f"--- Processing Request: {url} ---")
    is_tiktok = "tiktok" in url.lower()
    
    # Use a timestamp to keep filenames unique
    file_id = str(int(time.time()))
    
ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if is_tiktok else 'bestaudio/best',
        'ffmpeg_location': MY_FFMPEG_PATH,
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        # TRICK: This makes YouTube think you are a real browser
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    if not is_tiktok:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio', 
            'preferredcodec': 'mp3', 
            'preferredquality': '192'
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'download')
            safe_title = clean_filename(original_title)
            
            ext = "mp4" if is_tiktok else "mp3"
            final_path = f"{DOWNLOAD_FOLDER}/{file_id}.{ext}"
            download_name = f"{safe_title}.{ext}"

        if not os.path.exists(final_path):
            return "Error: File conversion failed (FFmpeg issue)", 500

        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(60) # Wait 1 minute then delete from server
                try:
                    if os.path.exists(final_path):
                        os.remove(final_path)
                except Exception as e:
                    print(f"Cleanup error: {e}")
            threading.Thread(target=delete_later).start()
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=download_name,
            mimetype='video/mp4' if is_tiktok else 'audio/mpeg'
        )
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    # Render's port is dynamic
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
