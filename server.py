import re
import json
import urllib.parse
import requests
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def search_youtube_innertube(query):
    """Buscador Antibloqueos (Funciona 100%)"""
    url = "https://www.youtube.com/youtubei/v1/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
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
        r = requests.post(url, json=payload, headers=headers, timeout=6)
        if r.status_code == 200:
            parse_items(r.json())
            if results:
                return results
    except Exception as e:
        print(f"Error InnerTube: {e}")

    try:
        scrape_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Cookie": "SOCS=CAI"
        }
        s_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        res = requests.get(s_url, headers=scrape_headers, timeout=6)
        match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', res.text)
        if match:
            data = json.loads(match.group(1))
            parse_items(data)
            if results:
                return results
    except Exception as e:
        print(f"Error Scraper: {e}")

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
    Cadena de Extracción Blindada:
    Usa múltiples APIs globales para evitar que Render sea detectado como bot.
    """
    
    # INTENTO 1: Cobalt API (Alta velocidad y estabilidad)
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "isAudioOnly": True,
            "aFormat": "mp3"
        }
        res = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            stream_url = data.get("url")
            if stream_url:
                return redirect(stream_url)
    except Exception as e:
        print(f"Cobalt falló: {e}")

    # INTENTO 2: Nodos Piped
    piped_nodes = [
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://pipedapi.tokhmi.xyz/streams/{video_id}",
        f"https://api.piped.projectsegfau.lt/streams/{video_id}",
        f"https://pipedapi.smnz.de/streams/{video_id}"
    ]
    
    for url in piped_nodes:
        try:
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                audio_streams = data.get('audioStreams', [])
                if audio_streams:
                    best_audio = sorted(audio_streams, key=lambda x: int(x.get('bitrate', 0)), reverse=True)
                    if best_audio:
                        return redirect(best_audio[0].get('url'))
        except Exception:
            continue

    # INTENTO 3: Nodos Invidious
    invidious_nodes = [
        f"https://inv.tux.pizza/api/v1/videos/{video_id}",
        f"https://invidious.weblibre.org/api/v1/videos/{video_id}",
        f"https://invidious.flokinet.to/api/v1/videos/{video_id}"
    ]
    
    for url in invidious_nodes:
        try:
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                adaptive = data.get('adaptiveFormats', [])
                audios = [f for f in adaptive if f.get('type', '').startswith('audio')]
                if audios:
                    best_audio = sorted(audios, key=lambda x: int(x.get('bitrate', 0)), reverse=True)
                    if best_audio:
                        return redirect(best_audio[0].get('url'))
        except Exception:
            continue

    # Si todo falla, no usamos yt-dlp para no generar error 500 por bot.
    return jsonify({'error': 'Servidores saturados temporalmente. Intenta nuevamente en unos segundos.'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
