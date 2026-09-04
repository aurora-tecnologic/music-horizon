
import os
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Opciones optimizadas con emulación Android/iOS para saltar el bloqueo 429 de YouTube
YDL_SEARCH_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
    'skip_download': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios']
        }
    }
}

YDL_STREAM_OPTS = {
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
    """Ruta base para evitar errores 404 en los logs de Render"""
    return jsonify({"status": "online", "service": "Music Horizon API"}), 200

@app.route('/api/search', methods=['POST'])
def search_tracks():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"results": []}), 200

    try:
        with yt_dlp.YoutubeDL(YDL_SEARCH_OPTS) as ydl:
            # Busca los primeros 6 resultados
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
        print(f"Error en /api/search: {e}")
        return jsonify({"results": [], "error": str(e)}), 500

@app.route('/api/stream/<video_id>', methods=['GET'])
def stream_audio(video_id):
    if not video_id:
        return jsonify({"error": "ID de video faltante"}), 400

    direct_url = None
    title = f"{video_id}.mp3"

    # 1. Intento primario: yt-dlp con emulación móvil
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(YDL_STREAM_OPTS) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            if info.get('title'):
                title = f"{info['title'][:50]}.mp3"
    except Exception as e:
        print(f"yt-dlp fallo (posible 429): {e}. Probando respaldo...")

    # 2. Respaldo secundario: Piped API pública si YouTube bloquea la IP de Render
    if not direct_url:
        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://api.piped.privacydev.net",
            "https://piped-api.lunar.icu"
        ]
        for instance in piped_instances:
            try:
                res = requests.get(f"{instance}/streams/{video_id}", timeout=5)
                if res.status_code == 200:
                    stream_data = res.json()
                    audio_streams = stream_data.get('audioStreams', [])
                    if audio_streams:
                        direct_url = audio_streams[-1].get('url')
                        title = f"{stream_data.get('title', video_id)[:50]}.mp3"
                        break
            except Exception:
                continue

    if not direct_url:
        return jsonify({"error": "No fue posible obtener el stream de audio"}), 500

    # 3. Transmisión fragmentada del audio hacia el navegador del celular
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }
        upstream_req = requests.get(direct_url, headers=headers, stream=True, timeout=10)

        def generate():
            for chunk in upstream_req.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk

        # Limpiar caracteres especiales para el encabezado del archivo
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_', '-')).strip()

        return Response(
            stream_with_context(generate()),
            content_type=upstream_req.headers.get('Content-Type', 'audio/mpeg'),
            headers={
                'Content-Disposition': f'attachment; filename="{safe_title}"',
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        print(f"Error retransmitiendo audio: {e}")
        return jsonify({"error": "Fallo al enviar datos del archivo"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
