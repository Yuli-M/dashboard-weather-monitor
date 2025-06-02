from api.database import db_manager
from api.models.payments import Payment
from datetime import datetime, timedelta
from typing import List, Optional

class PagoService:
    @staticmethod
    def obtener_por_usuario(user_id: str) -> List[Payment]:
        """Obtiene todos los pagos de un usuario desde Supabase"""
        try:
            response = db_manager.supabase.table('payments').select('*').eq('user_id', user_id).order('payment_date', desc=True).execute()
            
            return response.data
        except Exception as e:
            raise Exception(f"Error al obtener pagos: {str(e)}")

    @staticmethod
    def crear_pago(pago_data: dict) -> dict:
        """Crea un nuevo pago en Supabase con expires_at calculado"""
        try:
            expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
            pago = db_manager.supabase.table('payments').insert({
                    **pago_data,
                    'status': 'pending',
                    'expires_at': expires_at,
                    'payment_date': datetime.utcnow().isoformat()
                }).execute()
            
            return pago.data[0] if pago.data else None
        except Exception as e:
            raise Exception(f"Error al crear pago: {str(e)}")
        
    @staticmethod
    def actualizar_estado(pago_id: str, nuevo_estado: str) -> Optional[dict]:
        """Actualiza el estado de un pago y maneja la logica de activacion"""
        try:
            # atualizar el pago
            pago = db_manager.supabase.table('payments').update({
                    'status': nuevo_estado,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', pago_id).execute()
            
            if not pago.data:
                return None

            # si el pago se marca como 'paid', verificar expiracion
            if nuevo_estado == 'paid':
                pago_data = pago.data[0]
                user_id = pago_data['user_id']
                
                #calcular nueva fecha de expiracion (1 mes despues)
                new_expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
                
                #actualizar expires_at del pago
                db_manager.supabase.table('payments').update({'expires_at': new_expires_at}) .eq('id', pago_id).execute()
                
                #activar perfil del usuario
                db_manager.supabase.table('profiles').update({'active': True}).eq('id', user_id).execute()
            
            return pago.data[0]
        except Exception as e:
            raise Exception(f"Error al actualizar pago: {str(e)}")
        
    @staticmethod
    def verificar_pago_activo(user_id: str) -> bool:
        """Verifica si el usuario tiene un pago activo (no expirado)"""
        try:
            response = db_manager.supabase.table('payments').select('*').eq('user_id', user_id).eq('status', 'paid').gt('expires_at', datetime.utcnow().isoformat()).order('payment_date', desc=True).limit(1).execute()
            
            return len(response.data) > 0
        except Exception as e:
            raise Exception(f"Error al verificar pago activo: {str(e)}")