from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp
from youtubesearchpython import VideosSearch

app = Flask(__name__)
CORS(app)

# Configuracion estricta para descargas simulando un iPhone para evadir el bloqueo
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

    # Ping para despertar el servidor de Render
    if query == 'ping':
        return jsonify({"status": "ok", "message": "Render Server Awake"})

    if not query:
        return jsonify({'results': []}), 400
    
    try:
        # NUEVO MOTOR: Evita el bloqueo de bot de YouTube al buscar
        videosSearch = VideosSearch(query, limit = 15)
        results_raw = videosSearch.result()
        results = []
        
        for video in results_raw.get('result', []):
            vid_id = video.get('id')
            if vid_id:
                results.append({
                    'id': vid_id,
                    'youtubeId': vid_id,
                    'title': video.get('title', 'Sin título'),
                    'artist': video.get('channel', {}).get('name', 'Desconocido'),
                    'duration': video.get('duration', '0:00'),
                    'cover': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                })
        return jsonify({'results': results})
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({'results': [], 'error': str(e)}), 500

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
