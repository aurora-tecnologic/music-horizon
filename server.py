import re
import json
import urllib.parse
import requests
from flask import Flask, jsonify, request, redirect
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

    # Intento de extracción 1
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=6)
        if r.status_code == 200:
            parse_items(r.json())
            if results: return results
    except Exception:
        pass

    # Intento de extracción 2
    try:
        scrape_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": "SOCS=CAI"
        }
        s_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        res = requests.get(s_url, headers=scrape_headers, timeout=6)
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
    RESOLVEDOR DIRECTO DE ENLACES.
    Render no descarga nada, solo extrae un enlace de alta velocidad (Cobalt o Piped)
    y redirige a tu teléfono para que descargue el archivo sin Timeouts.
    """
    # INTENTO 1: Servidor Oficial Cobalt (Soporta CORS y entrega el MP3 directo)
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://cobalt.tools",
            "Referer": "https://cobalt.tools/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "isAudioOnly": True,
            "aFormat": "mp3"
        }
        res = requests.post("https://co.wuk.sh/api/json", json=payload, headers=headers, timeout=8)
        if res.status_code == 200:
            stream_url = res.json().get("url")
            if stream_url:
                # El redirect permite que `fetch` en tu celular siga la ruta automáticamente
                return redirect(stream_url)
    except Exception as e:
        print(f"Cobalt falló: {e}")

    # INTENTO 2: Servidores Piped Proxies (Soportan CORS nativamente)
    piped_nodes = [
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://pipedapi.tokhmi.xyz/streams/{video_id}",
        f"https://pipedapi.smnz.de/streams/{video_id}"
    ]
    
    for url in piped_nodes:
        try:
            res = requests.get(url, timeout=6)
            if res.status_code == 200:
                audio_streams = res.json().get('audioStreams', [])
                if audio_streams:
                    # Seleccionar la mejor calidad
                    best_audio = sorted(audio_streams, key=lambda x: int(x.get('bitrate', 0)), reverse=True)
                    if best_audio:
                        return redirect(best_audio[0].get('url'))
        except Exception:
            continue

    return jsonify({'error': 'Todos los servidores están saturados, intenta en 1 minuto.'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
