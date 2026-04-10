from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os, time, threading, shutil, re

app = Flask(__name__)

DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

MY_FFMPEG_PATH = "/usr/bin/ffmpeg"

def clean_filename(title):
    return re.sub(r'[^\w\- ]', '', title).strip()

@app.route('/')
def home():
    return "Ready"

@app.route('/download')
def master_download():
    url = request.args.get('url')
    if not url: return "No URL", 400

    # Ensure URL is clean
    url = url.strip()
    
    file_id = str(int(time.time()))
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': MY_FFMPEG_PATH,
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        # This fixes the "Urllib" and "Bot" errors by mimicking a real phone
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    }

    ydl_opts['postprocessors'] = [{
        'key': 'FFmpegExtractAudio', 
        'preferredcodec': 'mp3', 
        'preferredquality': '192'
    }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # The 'download=True' must be here to prevent the URL scheme error
            info = ydl.extract_info(url, download=True)
            safe_title = clean_filename(info.get('title', 'audio'))
            final_path = f"{DOWNLOAD_FOLDER}/{file_id}.mp3"
            
        @after_this_request
        def cleanup(response):
            def delete_later():
                time.sleep(60)
                if os.path.exists(final_path): os.remove(final_path)
            threading.Thread(target=delete_later).start()
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=f"{safe_title}.mp3",
            mimetype='audio/mpeg'
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {str(e)}", 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
