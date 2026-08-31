import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para Netlify

# Ruta de verificación de estado (¡Obligatoria para que el frontend detecte que está online!)
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Backend activo"})

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "¡El backend de Music Horizon está funcionando al 100%!"
    })

# Ruta de búsqueda conectada
@app.route('/api/search', methods=['POST'])
def search_music():
    data = request.get_json() or {}
    query = data.get('query', '').lower()
    
    # Catálogo base para la búsqueda
    mock_results = [
        {"id": 1, "title": "Neon Midnight", "artist": "Luna Vega", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/1789399b8-e820-4e63-a50d-b11ded66f9b1.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "genre": "electronic"},
        {"id": 2, "title": "Urban Pulse", "artist": "Kairo", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/149411c3b-6e85-47a8-9a82-9990eb95acde.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3", "genre": "urban"},
        {"id": 3, "title": "Cosmic Drift", "artist": "Stellaris", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/120d5c5d9-40af-4bea-beae-c86fd06ad39c.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3", "genre": "ambient"},
        {"id": 4, "title": "Golden Hour", "artist": "Aria Sol", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/1c74965db-f333-42ab-8b3e-e8b2b9070d7d.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", "genre": "pop"}
    ]
    
    if query:
        filtered = [t for t in mock_results if query in t['title'].lower() or query in t['artist'].lower()]
        return jsonify({"results": filtered if filtered else mock_results})
    
    return jsonify({"results": mock_results})

# Ruta de simulación de streaming de audio
@app.route('/api/stream/<int:track_id>', methods=['GET'])
def stream_track(track_id):
    # Redirige o provee la fuente de audio real
    audio_urls = {
        1: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        2: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        3: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        4: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
    }
    target_url = audio_urls.get(track_id, "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
    return jsonify({"streamUrl": target_url})

@app.route('/api/download', methods=['POST'])
def download_track():
    return jsonify({"success": True, "message": "Descarga procesada por el backend"})

@app.route('/api/mix', methods=['POST'])
def smart_mix():
    return jsonify({
        "tracks": [
            {"id": 1, "title": "Neon Midnight", "artist": "Luna Vega", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/1789399b8-e820-4e63-a50d-b11ded66f9b1.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"}
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
