from typing import List, Optional, Dict
from api.database import db_manager
from api.models.torres import Torre
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TorreService:
    @staticmethod
    def obtener_todas() -> List[Dict]:
        """Obtiene todas las torres desde Supabase"""
        try:
            print(">>> Ejecutando consulta a Supabase torres")  # pruebas
            response = db_manager.supabase.table('torres').select('*').execute()
            print(">>> Respuesta cruda de Supabase:", response)  
            print(">>> Datos recibidos:", response.data)  
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo torres: {str(e)}")
            raise

    @staticmethod
    def obtener_por_id(id_torre: str) -> Optional[Dict]:
        """Obtiene una torre especifica por ID"""
        try:
            response = db_manager.supabase.table('torres').select('*').eq('id_torre', id_torre).maybe_single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo torre {id_torre}: {str(e)}")
            raise

    @staticmethod
    def obtener_por_usuario(usuario_id: str) -> List[Dict]:
        """Obtiene torres asignadas a un usuario"""
        try:
            response = db_manager.supabase.table('torres').select('*').eq('usuario_asignado', usuario_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo torres para usuario {usuario_id}: {str(e)}")
            raise

    @staticmethod
    def crear_torre(torre_data: Dict) -> Dict:
        """Crea una nueva torre con validación"""
        try:
            required_fields = ['nombre', 'ubicacion', 'origen_datos']
            if not all(field in torre_data for field in required_fields):
                raise ValueError("Faltan campos requeridos")

            torre_data.update({
                'estado': 'Inactiva',
                'fecha_creacion': datetime.utcnow().isoformat(),
                'ultima_actualizacion': datetime.utcnow().isoformat()
            })

            response = db_manager.supabase.table('torres').insert(torre_data).execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creando torre: {str(e)}")
            raise

    @staticmethod
    def actualizar_estado(id_torre: str, nuevo_estado: str) -> Dict:
        """Actualiza el estado de una torre"""
        try:
            response = db_manager.supabase.table('torres').update({
                    'estado': nuevo_estado,
                    'ultima_actualizacion': datetime.utcnow().isoformat()
                }).eq('id_torre', id_torre).execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error actualizando torre {id_torre}: {str(e)}")
            raise


    @staticmethod
    def actualizar_torre(id_torre: str, updates: dict) -> dict:
        """Actualiza una torre existente"""
        try:
            if not updates:
                raise ValueError("No hay campos para actualizar")
            
            updates['ultima_actualizacion'] = datetime.utcnow().isoformat()
            
            response = db_manager.supabase.table('torres').update(updates).eq('id_torre', id_torre).execute()
                
            if not response.data:
                raise ValueError("Torre no encontrada")
                
            return response.data[0]
        except Exception as e:
            logger.error(f"Error actualizando torre {id_torre}: {str(e)}")
            raise