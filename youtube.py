from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# This is a public, free 'Cobalt' instance. 
# If this one ever gets slow, you can just swap the URL.
COBALT_API_URL = "https://api.cobalt.tools/api/json"

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    # These settings tell Cobalt to give us a high-quality MP3
    payload = {
        "url": url,
        "downloadMode": "audio",
        "audioFormat": "mp3",
        "audioBitrate": "192"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        # Step 1: Send the YouTube link to the Cobalt API
        response = requests.post(COBALT_API_URL, json=payload, headers=headers)
        data = response.json()

        # Step 2: Cobalt returns a direct download link
        if data.get("status") == "stream" or data.get("status") == "redirect":
            return data.get("url") # Just send the raw link back to your Shortcut
        else:
            return f"Error: {data.get('text', 'Unknown error')}", 500

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
