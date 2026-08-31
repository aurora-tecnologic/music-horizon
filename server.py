from flask import Flask, jsonify, request, redirect
import yt_dlp

app = Flask(__name__)

# Configuración robusta de yt-dlp para extracción de audio limpia
YDL_OPTIONS_AUDIO = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'extractaudio': True,
}

YDL_OPTIONS_SEARCH = {
    'format': 'best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch5',
}

@app.route('/api/search', methods=['GET'])
def search_tracks():
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
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'uploader': entry.get('uploader') or entry.get('channel'),
                        'duration': entry.get('duration', 0),
                        'thumbnail': entry.get('thumbnail')
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
