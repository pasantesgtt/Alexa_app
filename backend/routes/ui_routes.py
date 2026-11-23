from flask import Blueprint, jsonify
from backend.services.faqs_service import obtener_todas_las_faqs, obtener_faqs_por_categoria

ui_bp = Blueprint('ui_bp', __name__)

@ui_bp.route('/api/faqs', methods=['GET'])
def get_faqs():
    """Devuelve todo el catálogo de preguntas frecuentes."""
    return jsonify(obtener_todas_las_faqs())
