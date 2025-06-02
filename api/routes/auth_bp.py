from flask import Blueprint, request, jsonify
from api.database import db_manager
from api.services.auth_service import AuthService
from functools import wraps
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Token faltante"}), 401

        # Separar prefijo Bearer si presente
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Formato de token inválido"}), 401

        token = parts[1]

        try:
            user = db_manager.supabase.auth.get_user(token)
            if not user:
                return jsonify({"error": "Token inválido"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        #  adjuntar el usuario ?
        request.supabase_user = user
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        lastname = data.get('lastname')

        if not all([email, password, name]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        # Registrar usuario en Supabase Auth
        response = db_manager.supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name,
                    "lastname": lastname or ""
                }
            }
        })

        db_manager.supabase.table('profiles').insert({
            "id": response.user.id,
            "name": name,
            "lastname": lastname or "",
            "active": False,
            "role": "usuario",
            "updated_at": datetime.utcnow().isoformat()
        }).execute()


        return jsonify({
            "message": "Usuario registrado. Verifica tu email.",
            "user_id": response.user.id
        }), 201
    

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email y contraseña requeridos"}), 400

        response = AuthService.login(data['email'], data['password'])
        if not response or not hasattr(response, 'user'):
            return jsonify({"error": "Credenciales inválidas"}), 401

        # RLS ?
        profile = db_manager.supabase.table('profiles').select('*').eq('id', response.user.id).single().execute()

        # if not profile.data or not profile.data.get('active'):
        #     return jsonify({
        #         "error": "Cuenta inactiva",
        #         "requires_payment": True
        #     }), 403

        return jsonify({
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                **response.user.model_dump(),
                "role": profile.data.get('role', 'usuario')
            }
        })

    except Exception as e:
        return jsonify({"error": f"Error en el login: {str(e)}"}), 401

@auth_bp.route('/activate', methods=['POST'])
@jwt_required
def activate_account():

    
    # token = request.headers.get('Authorization')
    # user = db_manager.supabase.auth.get_user(token).user

    user = request.supabase_user.user

    try:
        #verificar pago existente
        payment = db_manager.supabase.table('payments').select('id, status').eq('user_id', user.id).eq('status', 'completed').execute()

        if not payment.data:
            return jsonify({"error": "Se requiere un pago completado para activar la cuenta"}), 402
        
        #verificar que el pago no haya expirado (si aplica) ?
        latest_payment = payment.data[0]
        if latest_payment.get('expires_at') and latest_payment['expires_at'] < datetime.now().isoformat():
            return jsonify({"error": "El pago ha expirado"}), 402
        
        #actualizar perfil
        db_manager.supabase.table('profiles').update({'active': True, 'updated_at': datetime.utcnow().isoformat()}).eq('id', user.id).execute()
        return jsonify({
            "message": "Cuenta activada con éxito",
            "payment_id": latest_payment['id']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    user = request.supabase_user.user

    try:
        # Obtener perfil del usuario
        profile = db_manager.supabase.table('profiles').select('*').eq('id', user.id).single().execute()


        torres = db_manager.supabase.table('torres').select('*').eq('usuario_asignado', user.id).execute()

        return jsonify({
            **user.model_dump(),
            "profile": profile.data,
            "torres": torres.data if torres.data else []
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # token = request.headers.get('Authorization')
    # try:
    #     user = supabase.auth.get_user(token)
    #     return jsonify(user.user.model_dump())
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 401


@auth_bp.route('/me', methods=['PUT'])
@jwt_required
def update_my_profile():
    user = request.supabase_user.user
    access_token = request.headers.get('Authorization').split()[1]  #  token real

    data = request.get_json()

    profile_updates = {}
    password_result = None

    # datos del perfil
    for field in ['name', 'lastname']:
        if field in data:
            profile_updates[field] = data[field]

    if profile_updates:
        try:
            AuthService.update_profile(user.id, profile_updates)
        except Exception as e:
            return jsonify({"error": f"Error actualizando perfil: {str(e)}"}), 400

    # Cambio de contrase;a si se envia current y new
    if 'new_password' in data and 'current_password' in data:
        password_result = AuthService.update_password_authenticated(
            access_token=access_token,
            current_password=data['current_password'],
            new_password=data['new_password']
        )

        if password_result['status'] == 'error':
            return jsonify(password_result), 400

    response = {"message": "Perfil actualizado correctamente"}
    if password_result:
        response["password_message"] = password_result['message']

    return jsonify(response)



@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    try:
        AuthService.logout()
        return jsonify({"message": "Sesión cerrada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    