from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp
import requests
import urllib.parse

app = Flask(__name__)
CORS(app)

YDL_OPTIONS_AUDIO = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'extractor_args': {'youtube': {'player_client': ['ios', 'android']}},
}

@app.route('/api/search', methods=['GET', 'POST'])
def search_tracks():
    query = ''
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '') or data.get('q', '')
    else:
        query = request.args.get('q', '')

    # Ping para mantener el servidor alerta
    if query == 'ping':
        return jsonify({"status": "ok", "message": "Render Server Awake"})

    if not query:
        return jsonify({'results': []}), 400
    
    encoded_query = urllib.parse.quote(query)
    results = []

    # INTENTO 1: Api Global Piped (Instantáneo y sin bloqueos)
    piped_nodes = [
        f"https://pipedapi.smnz.de/search?q={encoded_query}&filter=videos",
        f"https://pipedapi.tokhmi.xyz/search?q={encoded_query}&filter=videos",
        f"https://pipedapi.kavin.rocks/search?q={encoded_query}&filter=videos"
    ]
    
    for url in piped_nodes:
        try:
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                for item in data.get('items', [])[:15]:
                    vid_id = item.get('url', '').split('?v=')[-1]
                    if vid_id:
                        results.append({
                            'id': vid_id,
                            'youtubeId': vid_id,
                            'title': item.get('title', 'Sin título'),
                            'artist': item.get('uploaderName', 'Desconocido'),
                            'cover': item.get('thumbnail', f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg")
                        })
                if results:
                    return jsonify({'results': results})
        except Exception:
            continue

    # INTENTO 2: Api Global Invidious de respaldo
    invidious_nodes = [
        f"https://inv.tux.pizza/api/v1/search?q={encoded_query}&type=video",
        f"https://invidious.weblibre.org/api/v1/search?q={encoded_query}&type=video"
    ]
    for url in invidious_nodes:
        try:
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                for item in data[:15]:
                    vid_id = item.get('videoId')
                    if vid_id:
                        results.append({
                            'id': vid_id,
                            'youtubeId': vid_id,
                            'title': item.get('title', 'Sin título'),
                            'artist': item.get('author', 'Desconocido'),
                            'cover': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                        })
                if results:
                    return jsonify({'results': results})
        except Exception:
            continue
            
    # INTENTO 3: Último recurso directo al servidor
    try:
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch15',
            'extractor_args': {'youtube': {'player_client': ['android']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [info])
            for entry in entries:
                if entry and entry.get('id'):
                    vid_id = entry.get('id')
                    results.append({
                        'id': vid_id,
                        'youtubeId': vid_id,
                        'title': entry.get('title', 'Sin título'),
                        'artist': entry.get('uploader', 'Desconocido'),
                        'cover': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    })
        if results:
            return jsonify({'results': results})
    except Exception as e:
        print(f"Error en yt-dlp: {e}")
        
    return jsonify({'results': [], 'error': 'Servidores ocupados'}), 500

@app.route('/api/stream/<video_id>', methods=['GET'])
def stream_audio(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(YDL_OPTIONS_AUDIO) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            if not audio_url:
                raise Exception("URL de audio no encontrada")
            return redirect(audio_url)
    except Exception as e:
        print(f"Error al obtener stream de audio: {e}")
        return jsonify({'error': 'Bloqueo al descargar', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
