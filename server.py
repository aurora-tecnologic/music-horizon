from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Habilitar CORS para recibir peticiones desde tu Netlify

# Configuracion estricta para evadir bloqueos de bots de YouTube en servidores cloud (Render)
YDL_OPTIONS_AUDIO = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'extractaudio': True,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
}

YDL_OPTIONS_SEARCH = {
    'format': 'best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch10',
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
}

@app.route('/api/search', methods=['GET', 'POST'])
def search_tracks():
    query = ''
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '') or data.get('q', '')
    else:
        query = request.args.get('q', '')

    # Controlador del ping silencioso para despertar el servidor
    if query == 'ping':
        return jsonify({"status": "ok", "message": "Render Server Awake"})

    if not query:
        return jsonify({'results': []}), 400
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS_SEARCH) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [info])
            results = []
            
            for entry in entries:
                if entry and entry.get('id'):
                    vid_id = entry.get('id')
                    results.append({
                        'id': vid_id,
                        'youtubeId': vid_id,
                        'title': entry.get('title', 'Sin título'),
                        'artist': entry.get('uploader') or entry.get('channel') or 'Desconocido',
                        'duration': entry.get('duration', 0),
                        'cover': entry.get('thumbnail') or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    })
            return jsonify({'results': results})
    except Exception as e:
        print(f"Error en búsqueda en Render: {e}")
        return jsonify({'results': [], 'error': str(e)}), 500

@app.route('/api/stream/<video_id>', methods=['GET'])
def stream_audio(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(YDL_OPTIONS_AUDIO) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            if not audio_url:
                raise Exception("No se pudo extraer el stream directo de YouTube")
            # Redirige el reproductor o el gestor de descargas al archivo de audio real
            return redirect(audio_url)
    except Exception as e:
        print(f"Error al obtener stream de audio: {e}")
        return jsonify({'error': 'No se pudo procesar el audio por bloqueo de YouTube', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
