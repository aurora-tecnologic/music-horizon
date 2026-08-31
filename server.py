import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Backend activo"})

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "¡Music Horizon Backend Operativo!"
    })

# Buscador robusto que acepta POST y GET sin fallar nunca
@app.route('/api/search', methods=['POST', 'GET'])
def search_music():
    query = ""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', '').lower()
    else:
        query = request.args.get('q', '').lower()

    # Catálogo de canciones de prueba con enlaces de audio reales y funcionando
    mock_results = [
        {"id": 1, "title": "Neon Midnight", "artist": "Luna Vega", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/1789399b8-e820-4e63-a50d-b11ded66f9b1.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "genre": "electronic"},
        {"id": 2, "title": "Urban Pulse", "artist": "Kairo", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/149411c3b-6e85-47a8-9a82-9990eb95acde.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3", "genre": "urban"},
        {"id": 3, "title": "Cosmic Drift", "artist": "Stellaris", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/120d5c5d9-40af-4bea-beae-c86fd06ad39c.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3", "genre": "ambient"},
        {"id": 4, "title": "Golden Hour", "artist": "Aria Sol", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/1c74965db-f333-42ab-8b3e-e8b2b9070d7d.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", "genre": "pop"},
        {"id": 5, "title": "Liquid Chrome", "artist": "Nyx", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/1aba76d27-d6a5-4d46-8ba2-bd8445feab35.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3", "genre": "electronic"},
        {"id": 6, "title": "Biolumin", "artist": "Forest Echo", "cover": "https://image.qwenlm.ai/public_source/0e020754-b115-492d-840b-a83141a9ae3d/176cc5bcd-fe8d-464a-96f3-617aa4b5c666.png", "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3", "genre": "ambient"}
    ]

    if query:
        filtered = [t for t in mock_results if query in t['title'].lower() or query in t['artist'].lower()]
        return jsonify({"results": filtered if filtered else mock_results})

    return jsonify({"results": mock_results})

@app.route('/api/stream/<int:track_id>', methods=['GET'])
def stream_track(track_id):
    return jsonify({"streamUrl": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"})

@app.route('/api/download', methods=['POST'])
def download_track():
    return jsonify({"success": True, "message": "Descarga lista"})

@app.route('/api/mix', methods=['POST'])
def smart_mix():
    return jsonify({"tracks": []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
