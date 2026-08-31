import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir peticiones desde Netlify

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "¡El backend de Music Horizon está funcionando al 100%!"
    })

# Ruta de búsqueda de música
@app.route('/api/search', methods=['GET'])
def search_music():
    query = request.args.get('q', '')
    # Datos de ejemplo (Mock) para que la app responda de inmediato
    mock_results = [
        {"id": 1, "title": "Neon Midnight", "artist": "Luna Vega", "duration": "3:45"},
        {"id": 2, "title": "Urban Pulse", "artist": "Kairo", "duration": "4:12"},
        {"id": 3, "title": "Cosmic Drift", "artist": "Stellaris", "duration": "3:55"},
        {"id": 4, "title": "Golden Hour", "artist": "Aria Sol", "duration": "4:05"}
    ]
    return jsonify({"query": query, "results": mock_results})

# Ruta de historial de reproducción
@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({
        "history": [
            {"song": "Neon Midnight", "artist": "Luna Vega", "timestamp": "Hace un momento"}
        ]
    })

if __name__ == '__main__':
    # Render asigna un puerto automático mediante variables de entorno
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
