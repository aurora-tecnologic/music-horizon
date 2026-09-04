import os
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, expose_headers=["Content-Length", "Content-Disposition"])

# Opciones de extracción emulando clientes móviles para evadir bloqueos 429/403
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios']
        }
    }
}

@app.route('/', methods=['GET', 'HEAD'])
def health_check():
    return jsonify({"status": "online", "service": "Music Horizon API"}), 200

@app.route('/api/search', methods=['POST'])
def search_tracks():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"results": []}), 200

    try:
        search_opts = {**YDL_OPTS, 'extract_flat': True}
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch6:{query}", download=False)
            entries = search_results.get('entries', [])

            results = []
            for entry in entries:
                if not entry:
                    continue
                v_id = entry.get('id')
                results.append({
                    "id": v_id,
                    "youtubeId": v_id,
                    "title": entry.get('title', 'Sin título'),
                    "artist": entry.get('uploader') or entry.get('channel', 'Desconocido'),
                    "cover": f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                })
            return jsonify({"results": results}), 200
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({"results": [], "error": str(e)}), 500

@app.route('/api/stream/<video_id>', methods=['GET'])
def stream_audio(video_id):
    if not video_id:
        return jsonify({"error": "ID requerido"}), 400

    direct_url = None
    title = f"{video_id}.mp3"

    # 1. Extracción con yt-dlp
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            if info.get('title'):
                title = f"{info['title'][:50]}.mp3"
    except Exception as e:
        print(f"yt-dlp bloqueado ({e}), recurriendo a respaldo...")

    # 2. Respaldo secundario mediante API pública si YouTube bloquea la IP
    if not direct_url:
        fallbacks = [
            f"https://pipedapi.kavin.rocks/streams/{video_id}",
            f"https://api.piped.privacydev.net/streams/{video_id}"
        ]
        for api_url in fallbacks:
            try:
                r = requests.get(api_url, timeout=5)
                if r.status_code == 200:
                    streams = r.json().get('audioStreams', [])
                    if streams:
                        direct_url = streams[-1].get('url')
                        break
            except Exception:
                continue

    if not direct_url:
        return jsonify({"error": "Todos los servidores están saturados, intenta en 1 minuto."}), 500

    # 3. Envío del archivo en streaming continuo
    try:
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }
        upstream = requests.get(direct_url, headers=req_headers, stream=True, timeout=10)

        def generate():
            for chunk in upstream.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk

        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_', '-')).strip()

        resp_headers = {
            'Content-Disposition': f'attachment; filename="{safe_title}"',
            'Cache-Control': 'no-cache',
            'Access-Control-Expose-Headers': 'Content-Length, Content-Disposition'
        }
        if upstream.headers.get('Content-Length'):
            resp_headers['Content-Length'] = upstream.headers.get('Content-Length')

        return Response(
            stream_with_context(generate()),
            content_type=upstream.headers.get('Content-Type', 'audio/mpeg'),
            headers=resp_headers
        )
    except Exception as e:
        return jsonify({"error": f"Fallo al transmitir: {e}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
