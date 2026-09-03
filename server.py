import re
import json
import urllib.parse
import requests
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def search_youtube_innertube(query):
    """Buscador Antibloqueos de Alta Velocidad (Ya comprobado que funciona)"""
    url = "https://www.youtube.com/youtubei/v1/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "context": {
            "client": {
                "hl": "es",
                "gl": "CO",
                "clientName": "WEB",
                "clientVersion": "2.20240401.01.00"
            }
        },
        "query": query
    }
    
    results = []

    def parse_items(obj):
        if len(results) >= 15:
            return
        if isinstance(obj, dict):
            if 'videoId' in obj and ('title' in obj or 'headline' in obj):
                vid = obj.get('videoId')
                t_obj = obj.get('title') or obj.get('headline')
                title = ""
                if isinstance(t_obj, dict):
                    runs = t_obj.get('runs', [])
                    title = runs[0].get('text', '') if runs else t_obj.get('simpleText', '')
                elif isinstance(t_obj, str):
                    title = t_obj

                artist = "Desconocido"
                owner = obj.get('ownerText') or obj.get('shortBylineText')
                if owner and isinstance(owner, dict) and 'runs' in owner and owner['runs']:
                    artist = owner['runs'][0].get('text', 'Desconocido')

                if vid and title and not any(x['id'] == vid for x in results):
                    results.append({
                        'id': vid,
                        'youtubeId': vid,
                        'title': title,
                        'artist': artist,
                        'cover': f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                    })
            for v in obj.values():
                parse_items(v)
        elif isinstance(obj, list):
            for item in obj:
                parse_items(item)

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        if r.status_code == 200:
            parse_items(r.json())
            if results: return results
    except Exception:
        pass

    try:
        scrape_headers = {
            "User-Agent": "Mozilla/5.0",
            "Cookie": "SOCS=CAI"
        }
        s_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        res = requests.get(s_url, headers=scrape_headers, timeout=5)
        match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', res.text)
        if match:
            data = json.loads(match.group(1))
            parse_items(data)
            if results: return results
    except Exception:
        pass

    return []

@app.route('/api/search', methods=['GET', 'POST'])
def search_tracks():
    query = ''
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '') or data.get('q', '')
    else:
        query = request.args.get('q', '')

    if query == 'ping':
        return jsonify({"status": "ok", "message": "Render Server Awake"})

    if not query:
        return jsonify({'results': []}), 400

    results = search_youtube_innertube(query)
    return jsonify({'results': results})

@app.route('/api/stream/<video_id>', methods=['GET'])
def stream_audio(video_id):
    """
    MODO TÚNEL BLINDADO:
    1. Usa APIs globales especializadas en MP3 para evitar el bloqueo de Render.
    2. Transmite el archivo al celular en fragmentos para engañar la seguridad CORS del navegador.
    """
    stream_url = None

    # INTENTO 1: API Directa de MP3 (Ultra estable)
    try:
        res = requests.get(f"https://api.ryzendesu.vip/api/downloader/ytmp3?url=https://youtu.be/{video_id}", timeout=6)
        if res.status_code == 200:
            data = res.json()
            if data.get('success') and data.get('url'):
                stream_url = data.get('url')
    except Exception as e:
        print(f"Ryzendesu falló: {e}")

    # INTENTO 2: Nodos Piped Oficiales
    if not stream_url:
        piped_nodes = [
            "https://pipedapi.kavin.rocks",
            "https://pipedapi.tokhmi.xyz",
            "https://api.piped.projectsegfau.lt"
        ]
        for node in piped_nodes:
            try:
                res = requests.get(f"{node}/streams/{video_id}", timeout=5)
                if res.status_code == 200:
                    audio_streams = res.json().get('audioStreams', [])
                    if audio_streams:
                        best = sorted(audio_streams, key=lambda x: int(x.get('bitrate', 0)), reverse=True)
                        stream_url = best[0].get('url')
                        if stream_url: break
            except Exception:
                continue

    # INTENTO 3: YT-DLP Seguro (Cliente iOS para evadir bot block)
    if not stream_url:
        try:
            import yt_dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'skip_download': True,
                'extractor_args': {'youtube': {'player_client': ['ios']}}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                stream_url = info.get('url')
        except Exception as e:
            print(f"yt-dlp falló: {e}")

    # Si definitivamente fallan las 3 capas:
    if not stream_url:
        return jsonify({'error': 'Todos los servidores están saturados, intenta en 1 minuto.'}), 500

    # EL TRUCO DE LA TRANSMISIÓN EN FRAGMENTOS
    try:
        req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(stream_url, stream=True, headers=req_headers, timeout=10)
        
        # Si YouTube devuelve 403, significa que el enlace caducó
        if r.status_code != 200:
            return jsonify({'error': f'Acceso denegado al archivo (Error {r.status_code})'}), 500
            
        def generate():
            # Pasamos la canción al celular en bloques de 1MB para mantener la conexión viva
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    yield chunk

        # Al usar Response, el archivo adquiere permisos libres (CORS *) y tu celular lo acepta de inmediato
        response = Response(
            stream_with_context(generate()), 
            content_type=r.headers.get('content-type', 'audio/mpeg')
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{video_id}.mp3"'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print(f"Error transfiriendo al celular: {e}")
        return jsonify({'error': 'Fallo al procesar el archivo en el servidor proxy.'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
