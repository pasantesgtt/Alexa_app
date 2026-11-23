from flask import Blueprint, request, Response, stream_with_context
from backend.services.api_gateway import Api_gateway

chat_bp = Blueprint('chat', __name__)
api_gateway = Api_gateway()

@chat_bp.route('/api/chat/preguntar', methods=['POST'])
def preguntar():
    datos = request.json
    pregunta = datos.get("pregunta", "")
    session_id = datos.get("session_id", "kiosko_1")
    sede = datos.get("sede", "panoptico") # <-- Atrapar la sede

    # 1. Delegamos la lógica de conexión y timeout a la capa de servicios
    generador = api_gateway.consultar_cerebro_stream(session_id, pregunta, sede)

    # 2. Retornamos la respuesta en streaming puro
    return Response(stream_with_context(generador), mimetype='text/plain')