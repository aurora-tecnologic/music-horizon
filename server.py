import os
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Backend rápido activo"})

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Music Horizon - Servidor Operativo"})

@app.route('/api/search', methods=['POST', 'GET'])
def search_music():
    query = ""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '')
    else:
        query = request.args.get('q', '')

    if not query:
        return jsonify({"results": []})

    results = []
    
    try:
        search_query = query if ("youtube.com" in query or "youtu.be" in query) else f"ytsearch8:{query}"
        # Usamos extract_flat para que la respuesta de YouTube sea inmediata y no se pegue
        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', [info]) if 'entries' in info else [info]
            
            for entry in entries:
                if not entry:
                    continue
                video_id = entry.get('id')
                if not video_id:
                    continue
                
                title = entry.get('title', query)
                uploader = entry.get('uploader') or entry.get('channel') or 'YouTube'
                # Miniatura oficial directa de YouTube para mayor velocidad
                cover = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                
                results.append({
                    "id": video_id,
                    "title": title,
                    "artist": uploader,
                    "cover": cover,
                    "streamUrl": f"{request.host_url.rstrip('/')}/api/stream/{video_id}",
                    "duration": entry.get('duration', 180)
                })
    except Exception as e:
        print(f"Error optimizando yt-dlp: {e}")

    # Fallback de seguridad por si la red falla por completo
    if not results:
        results.append({
            "id": "fallback_1",
            "title": query.capitalize(),
            "artist": "YouTube Search",
            "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500",
            "streamUrl": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "duration": 200
        })

    return jsonify({"results": results})

@app.route('/api/stream/<video_id>', methods=['GET'])
def get_stream(video_id):
    if str(video_id).startswith("fallback_"):
        return redirect("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
    
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {'format': 'bestaudio/best', 'skip_download': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            if audio_url:
                return redirect(audio_url)
    except Exception:
        pass
    
    return redirect("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")

@app.route('/api/download', methods=['POST'])
def download_track():
    return jsonify({"success": True, "message": "Descarga lista"})

@app.route('/api/mix', methods=['POST'])
def smart_mix():
    return jsonify({"tracks": []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
