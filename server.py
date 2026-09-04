import os
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, expose_headers=["Content-Length", "Content-Disposition"])

# Clientes que no requieren PO-Token y evaden la detección de bot en datacenters
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'nocheckcertificate': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['ios', 'tv_embedded', 'mweb'],
            'player_skip': ['webpage', 'configs']
        }
    }
}

INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://invidious.drgns.space",
    "https://yt.artemislena.eu",
    "https://invidious.private.coffee"
]

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
        return jsonify({"error": "ID de video faltante"}), 400

    direct_url = None
    title = f"{video_id}.mp3"

    # 1. Extracción primaria con yt-dlp usando clientes iOS y TV Embed
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            if info.get('title'):
                title = f"{info['title'][:50]}.mp3"
    except Exception as e:
        print(f"yt-dlp bloqueado en Render ({e}), intentando servidores proxy...")

    # 2. Respaldo Invidious con local=true (fuerza al proxy a emitir el audio sin dar 403)
    if not direct_url:
        for instance in INVIDIOUS_INSTANCES:
            try:
                proxy_url = f"{instance}/latest_version?id={video_id}&itag=140&local=true&listen=1"
                r = requests.head(proxy_url, timeout=4, allow_redirects=True)
                if r.status_code == 200:
                    direct_url = proxy_url
                    break
            except Exception:
                continue

    # 3. Respaldo secundario mediante Cobalt API
    if not direct_url:
        cobalt_nodes = [
            "https://cobalt-api.kwiatekm.me",
            "https://api.wuk.sh"
        ]
        for node in cobalt_nodes:
            try:
                res = requests.post(f"{node}/", json={
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "downloadMode": "audio"
                }, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=5)
                data = res.json()
                if "url" in data:
                    direct_url = data["url"]
                    break
            except Exception:
                continue

    if not direct_url:
        return jsonify({"error": "Servidores temporalmente saturados. Intenta de nuevo en unos segundos."}), 503

    # 4. Transmisión del flujo hacia el navegador
    try:
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        upstream = requests.get(direct_url, headers=req_headers, stream=True, timeout=12)
        if upstream.status_code != 200:
            return jsonify({"error": "Fuente de audio inaccesible"}), 502

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
