from flask import Flask, request, send_file, after_this_request
import yt_dlp
import os, time, threading

app = Flask(__name__)
DOWNLOAD_FOLDER = '/tmp/tiktok'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home(): return "TikTok Service Online"

@app.route('/download')
def tiktok_download():
    url = request.args.get('url')
    if not url: return "No URL", 400
    
    file_id = str(int(time.time()))
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{DOWNLOAD_FOLDER}/{file_id}.mp4"

        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(60), os.remove(filename) if os.path.exists(filename) else None)).start()
            return response

        return send_file(filename, as_attachment=True, download_name="tiktok_video.mp4")
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
