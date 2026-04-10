from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os
import time
import threading
import shutil

app = Flask(__name__)

# Render uses a temporary disk, so we use /tmp for downloads
DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Find FFmpeg automatically on Render
MY_FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"

@app.route('/')
def home():
    return "Render Downloader is Online! Use /download?url=..."

@app.route('/download')
def master_download():
    url = request.args.get('url')
    if not url:
        return "Error: No URL provided", 400

    print(f"--- Request Received for: {url} ---")
    is_tiktok = "tiktok" in url.lower()
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if is_tiktok else 'bestaudio/best',
        'ffmpeg_location': MY_FFMPEG_PATH,
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'merge_output_format': 'mp4' if is_tiktok else None,
        'noplaylist': True,
        'quiet': False,
    }

    if not is_tiktok:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio', 
            'preferredcodec': 'mp3', 
            'preferredquality': '192'
        }, {'key': 'EmbedThumbnail'}, {'key': 'FFmpegMetadata'}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            temp_filename = ydl.prepare_filename(info)
            ext = ".mp4" if is_tiktok else ".mp3"
            final_filename = os.path.splitext(temp_filename)[0] + ext

        # Auto-delete from Render's disk after 50 seconds to save space
        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(50)
                try:
                    if os.path.exists(final_filename):
                        os.remove(final_filename)
                        print(f"Cleaned up: {final_filename}")
                    # Remove thumbnails
                    base = os.path.splitext(final_filename)[0]
                    for t_ext in ['.jpg', '.png', '.webp', '.jpeg']:
                        if os.path.exists(base + t_ext):
                            os.remove(base + t_ext)
                except Exception as e:
                    print(f"Cleanup error: {e}")
            threading.Thread(target=delete_later).start()
            return response

        return send_file(
            final_filename, 
            as_attachment=True, 
            download_name=os.path.basename(final_filename),
            mimetype='video/mp4' if is_tiktok else 'audio/mpeg'
        )
        
    except Exception as e:
        print(f"RENDER ERROR: {e}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Render manages the port via an environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
