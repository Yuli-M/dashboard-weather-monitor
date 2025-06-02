# api/routes/estadisticas_bp.py
from flask import Blueprint, jsonify, request
from api.database import storage_manager, db_manager
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from api.services.datos_service import DatosService
from api.routes.auth_bp import jwt_required

estadisticas_bp = Blueprint('estadisticas', __name__)

@estadisticas_bp.route('/<id_torre>/resumen', methods=['GET'])
@jwt_required
def resumen_torre(id_torre):
    try:
        # Parametros opcionales
        horas = int(request.args.get('horas', 24))
        if horas > 168:  # Limite de 1 semana
            return jsonify({"error": "El rango máximo es 168 horas (7 días)"}), 400

        # Obtener estadísticas
        stats = DatosService.calcular_estadisticas(id_torre, horas)
        if not stats:
            return jsonify({"error": "No se encontraron datos"}), 404

        # Obtener diagnostico tecnico
        diagnostico = DatosService.obtener_diagnostico(id_torre)
        
        return jsonify({
            "estadisticas": stats,
            "diagnostico": diagnostico,
            "torre_id": id_torre
        })

    except ValueError:
        return jsonify({"error": "Parámetro 'horas' debe ser un número"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@estadisticas_bp.route('/<id_torre>/ultimos', methods=['GET'])
@jwt_required
def obtener_ultimos_datos(id_torre):
    try:
        horas = int(request.args.get('horas', 24))
        datos = DatosService.obtener_ultimos(id_torre, horas)
        return jsonify({
            "datos": datos,
            "count": len(datos)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500