from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

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

    if not query:
        return jsonify({'results': []}), 400
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS_SEARCH) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [info])
            results = []
            
            for entry in entries:
                if entry:
                    vid_id = entry.get('id')
                    if vid_id:
                        results.append({
                            'id': vid_id,
                            'youtubeId': vid_id,
                            'title': entry.get('title'),
                            'artist': entry.get('uploader') or entry.get('channel') or 'Desconocido',
                            'duration': entry.get('duration', 0),
                            'cover': entry.get('thumbnail') or f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg"
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
            return redirect(audio_url)
    except Exception as e:
        print(f"Error al obtener stream de audio: {e}")
        return jsonify({'error': 'No se pudo procesar el audio'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
