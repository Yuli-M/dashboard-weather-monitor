from flask import Blueprint, request, jsonify
from api.services.auth_service import AuthService
from api.routes.auth_bp import jwt_required
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

password_bp = Blueprint('password', __name__)

@password_bp.route('/update', methods=['POST'])
@jwt_required
def update_password():
    """
    Actualiza contraseña (usuario autenticado)
    Requiere:
    - Header 'Authorization: Bearer <JWT>'
    - Body con current_password y new_password
    """
    try:
        data = request.get_json()
        required = ['current_password', 'new_password']
        
        if not all(field in data for field in required):
            return jsonify({
                "status": "error",
                "message": "Contraseña actual y nueva contraseña requeridas",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
            
        if len(data['new_password']) < 8:
            return jsonify({
                "status": "error",
                "message": "La contraseña debe tener al menos 8 caracteres",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
        
        # Obtener token del header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Token requerido",
                "timestamp": datetime.utcnow().isoformat()
            }), 401
            
        token = auth_header.split()[1]  # Extraer el token despues de Bearer
        
        #llamar al servicio
        result = AuthService.update_password_authenticated(
            access_token=token,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if result['status'] == 'error':
            return jsonify({
                **result,
                "timestamp": datetime.utcnow().isoformat()
            }), 400
            
        return jsonify({
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error actualizando contraseña: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error al actualizar contraseña",
            "timestamp": datetime.utcnow().isoformat()
        }), 500