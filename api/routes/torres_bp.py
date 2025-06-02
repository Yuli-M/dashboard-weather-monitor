# api/routes/torres.py
from flask import Blueprint, jsonify, request
# from api.services.torre_service import crear_torre
from api.database import db_manager
from api.services import (
    torre_service,
    datos_service,
    diagnostico_service,
)
    
from api.routes.auth_bp import jwt_required

torres_bp = Blueprint('torres', __name__)
@torres_bp.route('/', methods=['GET'])
@jwt_required
def obtener_torres():
    """Obtiene todas las torres (con paginacion)"""
    try:
        print(">>> Iniciando obtención de torres")  # pruebas
        torres = torre_service.TorreService.obtener_todas()
        print(">>> Torres obtenidas:", torres)  
        
        return jsonify({
            "torres": torres,
            "count": len(torres),
            "page": 1,
            "status": "success"
        })
    except Exception as e:
        print(">>> Error en endpoint:", str(e))  #  ?
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@torres_bp.route('/<id_torre>', methods=['GET'])
@jwt_required
def obtener_torre(id_torre):
    """Obtiene una torre con su estado completo"""
    try:
        torre = torre_service.TorreService.obtener_por_id(id_torre)
        if not torre:
            return jsonify({"error": "Torre no encontrada"}), 404
        
        diagnostico = diagnostico_service.DiagnosticoService.obtener_ultimo(id_torre)
        estadisticas = datos_service.DatosService.calcular_estadisticas(id_torre)
        
        return jsonify({
            "torre": torre,
            "diagnostico": diagnostico,
            "estadisticas": estadisticas
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@torres_bp.route('/<id_torre>/datos', methods=['GET'])
@jwt_required
def obtener_datos_torre(id_torre):
    """Obtiene datos meteorológicos de una torre"""
    try:
        horas = min(int(request.args.get('horas', 24)), 168)  # Maximo 1 semana
        datos = datos_service.DatosService.obtener_ultimos(id_torre, horas)
        return jsonify({
            "data": datos,
            "meta": {
                "count": len(datos),
                "horas": horas,
                "torre_id": id_torre
            }
        })
    except ValueError:
        return jsonify({"error": "Parámetro 'horas' debe ser un número"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@torres_bp.route('/<id_torre>/diagnostico', methods=['GET'])
@jwt_required
def obtener_diagnostico(id_torre):
    """Obtiene el historial de diagnósticos técnicos"""
    try:
        limit = min(int(request.args.get('limit', 10)), 100)
        diagnosticos = diagnostico_service.DiagnosticoService.obtener_historico(id_torre, limit)
        return jsonify({
            "data": diagnosticos,
            "meta": {
                "count": len(diagnosticos),
                "torre_id": id_torre
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@torres_bp.route('/', methods=['POST']) #POST a la coleccion de torres
@jwt_required
def crear_torre():
    """Crea una nueva torre"""
    try:
        data = request.get_json()
        required_fields = ['nombre', 'ubicacion']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Campos requeridos: {required_fields}"}), 400
        
        torre = torre_service.TorreService.crear_torre(data)
        return jsonify({"data": torre}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@torres_bp.route('/<id_torre>/estado', methods=['PUT'])
@jwt_required
def actualizar_estado(id_torre):
    """Actualiza el estado de una torre"""
    try:
        nuevo_estado = request.json.get('estado')
        if not nuevo_estado:
            return jsonify({"error": "Campo 'estado' es requerido"}), 400
            
        torre = torre_service.TorreService.actualizar_estado(id_torre, nuevo_estado)
        return jsonify(torre)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@torres_bp.route('/<id_torre>', methods=['PUT'])
def actualizar_torre(id_torre):
    """Actualiza una torre existente"""
    try:
        data = request.get_json()
        allowed_fields = ['nombre', 'ubicacion', 'estado', 'origen_datos']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({"error": "No se proporcionaron campos válidos para actualizar"}), 400
            
        torre = torre_service.TorreService.actualizar_torre(id_torre, updates)
        return jsonify({"data": torre})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
