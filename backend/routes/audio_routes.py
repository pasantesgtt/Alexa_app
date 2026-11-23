import os
from flask import Blueprint, request, jsonify
from backend.services.stt_service import STTService
from backend.services.tts_service import TTSService  # <-- 1. Importamos el motor de voz

audio_bp = Blueprint('audio', __name__)

# Instanciamos los servicios
stt_service = STTService()
tts_luminito = TTSService(voice="es-CO-SalomeNeural")  # <-- 2. Inicializamos la voz colombiana

# Carpeta temporal para guardar los audios mientras se procesan
TEMP_DIR = os.path.join(os.getcwd(), 'backend', 'data', 'temp_audio')
os.makedirs(TEMP_DIR, exist_ok=True)

@audio_bp.route('/api/audio/transcribe', methods=['POST'])
def transcribir():
    # 1. Verificamos que el frontend nos haya enviado un archivo llamado 'audio'
    if 'audio' not in request.files:
        return jsonify({'error': 'No se recibió ningún archivo de audio'}), 400
    
    archivo_audio = request.files['audio']
    if archivo_audio.filename == '':
        return jsonify({'error': 'Archivo de audio vacío'}), 400

    try:
        # 2. Guardamos el audio temporalmente en nuestro disco
        ruta_temp = os.path.join(TEMP_DIR, 'grabacion_temp.webm')
        archivo_audio.save(ruta_temp)

        # 3. Le pasamos el archivo a nuestro motor de Whisper
        texto_transcrito = stt_service.transcribir_audio(ruta_temp)

        # 4. Limpiamos la basura: borramos el archivo de audio
        if os.path.exists(ruta_temp):
            try:
                os.remove(ruta_temp)
            except:
                pass

        # 5. Le devolvemos el texto limpio a la página web
        return jsonify({'texto': texto_transcrito})

    except Exception as e:
        return jsonify({'error': f'Error al procesar el audio: {str(e)}'}), 500

# ==========================================
# NUEVAS RUTAS DE VOZ (TTS)
# ==========================================

@audio_bp.route('/api/audio/hablar', methods=['POST'])
def reproducir_voz():
    datos = request.get_json()
    texto = datos.get("texto", "")
    
    if texto:
        # Dispara el audio en los parlantes del Raspberry
        tts_luminito.hablar(texto) 
        
    return jsonify({"status": "ok"})

@audio_bp.route('/api/chat/stop', methods=['POST'])
def detener_voz():
    # Calla a Luminito si el ciudadano vuelve a presionar espacio
    tts_luminito.detener_audio()
    return jsonify({"status": "silenciado"})