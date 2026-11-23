import os
import time
from dotenv import load_dotenv
from flask import Flask, send_from_directory, jsonify

# 1. Cargar variables de entorno obligatoriamente antes de arrancar nada
load_dotenv()

# 2. Importaciones de rutas y servicios
from backend.routes.chat_routes import chat_bp
from backend.routes.audio_routes import audio_bp
from backend.services.display_service import estado_sistema, registrar_interaccion, iniciar_servicio_pantalla

app = Flask(__name__, static_folder='frontend', static_url_path='')

app.register_blueprint(chat_bp)
app.register_blueprint(audio_bp)


# Arrancar el hilo del sensor de presencia en segundo plano
iniciar_servicio_pantalla()

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/sistema/estado', methods=['GET'])
def obtener_estado_sistema():
    return jsonify(estado_sistema)

@app.route('/api/sistema/interaccion', methods=['POST'])
def ruta_registrar_interaccion():
    # Usamos el método oficial en lugar de modificar el diccionario directamente
    registrar_interaccion()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # Usamos el puerto del entorno o 5000 por defecto
    port = int(os.getenv("PORT", 5001))
    debug_mode = os.getenv("FLASK_ENV") == "development"
    
    print(f"🚀 Iniciando Kiosco en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)