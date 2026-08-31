import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Backend con YouTube Activo"})

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Music Horizon - Motor YouTube Activo"})

# Buscador inteligente conectado 100% a YouTube
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

    # Si el usuario pegó una URL directa de YouTube
    if "youtube.com" in query or "youtu.be" in query:
        search_query = query
    else:
        # Búsqueda general (YouTube maneja la corrección de ortografía automáticamente)
        search_query = f"ytsearch10:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_flat': False,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
            # Si es una lista de resultados (búsqueda)
            entries = info.get('entries', [info]) if 'entries' in info else [info]
            
            for entry in entries:
                if not entry:
                    continue
                results.append({
                    "id": entry.get('id'),
                    "title": entry.get('title'),
                    "artist": entry.get('uploader') || entry.get('channel') || 'Desconocido',
                    "cover": entry.get('thumbnail') || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500',
                    "streamUrl": entry.get('url'), # URL directa de streaming de audio/video
                    "duration": entry.get('duration', 0),
                    "is_video": True if entry.get('duration', 0) > 600 else False # Detectar si es video largo o canción
                })
    except Exception as e:
        print(f"Error en búsqueda de YouTube: {e}")

    return jsonify({"results": results})

@app.route('/api/stream/<video_id>', methods=['GET'])
def get_stream(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {'format': 'bestaudio/best', 'skip_download': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({"streamUrl": info.get('url')})
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
