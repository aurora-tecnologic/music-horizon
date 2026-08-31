import os
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Backend activo"})

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Music Horizon Backend Operativo"})

@app.route('/api/search', methods=['POST', 'GET'])
def search_youtube():
    query = ""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '')
    else:
        query = request.args.get('q', '')

    if not query:
        return jsonify({"results": []})

    search_query = query if ("youtube.com" in query or "youtu.be" in query) else f"ytsearch10:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_flat': False,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    }

    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', [info]) if 'entries' in info else [info]
            
            for entry in entries:
                if not entry:
                    continue
                video_id = entry.get('id')
                results.append({
                    "id": video_id,
                    "title": entry.get('title'),
                    "artist": entry.get('uploader') or entry.get('channel') or 'Desconocido',
                    "cover": entry.get('thumbnail') or 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500',
                    # Apuntamos directamente a la ruta de streaming del backend
                    "streamUrl": f"{request.host_url.rstrip('/')}/api/stream/{video_id}",
                    "duration": entry.get('duration', 0)
                })
    except Exception as e:
        print(f"Error en yt-dlp: {e}")

    return jsonify({"results": results})

# Endpoint clave: Extrae el enlace en vivo de YouTube y redirige el audio al navegador
@app.route('/api/stream/<video_id>', methods=['GET'])
def get_stream(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': 'bestaudio/best', 
            'skip_download': True, 
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            if not audio_url:
                return jsonify({"error": "No se pudo obtener el stream"}), 404
            # Redirección oficial para que el reproductor HTML5 lea el audio real
            return redirect(audio_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/download', methods=['POST'])
def download_track():
    return jsonify({"success": True, "message": "Descarga procesada"})

@app.route('/api/mix', methods=['POST'])
def smart_mix():
    return jsonify({"tracks": []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
