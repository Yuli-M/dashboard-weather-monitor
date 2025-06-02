from api.database import db_manager
from flask import current_app
from supabase.lib.client_options import ClientOptions
from datetime import datetime

class AuthService:
    @staticmethod
    def login(email: str, password: str):
        try:
            response = db_manager.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response  #devuelve el objeto completo directamente
        except Exception as e:
            raise Exception(f"Error en login: {str(e)}")  # Mejor para manejo centralizado

    @staticmethod
    def get_user(token: str):
        return db_manager.supabase.auth.get_user(token)

    @staticmethod
    def logout():
        return db_manager.supabase.auth.sign_out()

    @staticmethod
    def update_profile(user_id: str, profile_data: dict):
        return db_manager.supabase.table('profiles').update(profile_data).eq('id', user_id).execute()
    
    @staticmethod
    def send_password_reset(email: str):
        """Envía email para resetear contraseña"""
        supabase = db_manager.supabase
        
        try:
            # Método nativo del cliente Supabase
            response = supabase.auth.reset_password_email(email)
            return {"status": "success", "message": "Correo de recuperación enviado"}
            
        except Exception as e:
            current_app.logger.error(f"Error enviando correo de recuperación: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def update_password(access_token: str, new_password: str):
        """Actualiza la contraseña con token válido"""
        supabase = db_manager.supabase
        
        try:
            response = supabase.auth.update_user(
                {"password": new_password},
                access_token=access_token
            )
            return {"status": "success", "data": response.user}
        except Exception as e:
            current_app.logger.error(f"Error actualizando contraseña: {str(e)}")
            return {"status": "error", "message": str(e)}
        

    @staticmethod
    def update_password_authenticated(access_token: str, current_password: str, new_password: str) -> dict:
        """Actualiza contraseña para usuario ya autenticado"""
        try:
            # reautenticacion
            db_manager.supabase.auth.sign_in_with_password({
                "email": db_manager.supabase.auth.get_user(access_token).user.email,
                "password": current_password
            })

            # verificar contrase;a actual
            user = db_manager.supabase.auth.get_user(access_token)
            if not user:
                return {"status": "error", "message": "Token inválido"}
            
            # Actualizar contrase;a
            db_manager.supabase.auth.update_user(
                {"password": new_password},
                access_token=access_token
            )
            
            return {"status": "success", "message": "Contraseña actualizada"}
        except Exception as e:
            return {"status": "error", "message": str(e)}