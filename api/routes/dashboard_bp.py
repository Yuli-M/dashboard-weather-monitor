# api/routes/dashboard.py
from flask import Blueprint, jsonify
from api.services import torre_service, diagnostico_service, datos_service
from api.routes.auth_bp import jwt_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/usuario/<usuario_id>', methods=['GET'])
@jwt_required
def dashboard_usuario(usuario_id):
    """Endpoint completo para el dashboard de usuario"""
    try:
        # obtener torres asignadas
        torres = torre_service.TorreService.obtener_por_usuario(usuario_id)
        if not torres:
            return jsonify({"error": "Usuario no tiene torres asignadas"}), 404
        
        resumen = []
        
        # procesar cada torre
        for torre in torres:
            # Datos meteorologicos (ultimas 24h)
            datos = datos_service.DatosService.obtener_ultimos(torre['id_torre'], 24)
            
            # diagnostico tecnico
            diagnostico = diagnostico_service.DiagnosticoService.obtener_ultimo(torre['id_torre'])
            
            # estadisticas basicas
            stats = {
                'muestras': len(datos),
                'ultima_lectura': datos[0]['timestamp'] if datos else None
            }
            
            resumen.append({
                "torre": torre,
                "diagnostico": diagnostico,
                "estadisticas": stats,
                "datos_recientes": datos[:5]  #  5 muestras?
            })
        
        return jsonify({
            "usuario_id": usuario_id,
            "total_torres": len(torres),
            "torres": resumen
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/torre/<torre_id>', methods=['GET'])
@jwt_required
def dashboard_torre(torre_id):
    """Endpoint detallado para una torre específica"""
    try:
        # Verificar torre
        torre = torre_service.TorreService.obtener_por_id(torre_id)
        if not torre:
            return jsonify({"error": "Torre no encontrada"}), 404
        
        # Obtener todos los datos
        datos = datos_service.DatosService.obtener_ultimos(torre_id, 48)  # Ultimas 48h
        diagnostico = diagnostico_service.DiagnosticoService.obtener_estado_general(torre_id)
        historico_diagnosticos = diagnostico_service.DiagnosticoService.obtener_historico(torre_id, 10)
        
        return jsonify({
            "torre": torre,
            "diagnostico_actual": diagnostico,
            "ultimos_diagnosticos": historico_diagnosticos,
            "datos": {
                "count": len(datos),
                "muestras": datos
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500