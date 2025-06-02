from api.database import db_manager
from api.models.diagnostico_tecnico import DiagnosticoTecnico
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class DiagnosticoService:
    @staticmethod
    def obtener_ultimo(id_torre: str) -> Optional[Dict]:
        """Obtiene el último diagnóstico técnico de Supabase"""
        try:
            response = db_manager.supabase.table('diagnostico_tecnico').select('*').eq('id_torre', id_torre).order('timestamp', desc=True).limit(1).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error obteniendo diagnóstico: {str(e)}")
            raise


    @staticmethod
    def obtener_historico(id_torre: str, limite: int = 100) -> List[Dict]:
        """Obtiene el historial de diagnósticos"""
        try:
            response = db_manager.supabase.table('diagnostico_tecnico').select('*').eq('id_torre', id_torre).order('timestamp', desc=True).limit(limite).execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo histórico: {str(e)}")
            raise

    @staticmethod
    def guardar_diagnostico(data: Dict) -> Dict:
        """Guarda un diagnóstico usando el storage_manager"""
        try:
            if 'id_torre' not in data:
                raise ValueError("El diagnóstico debe contener un id_torre")
            
            data['timestamp'] = data.get('timestamp') or datetime.utcnow().isoformat()
            
            # para guardar en todas las capas
            result = db_manager.storage_manager.save('diagnostico', data)
            
            if not all(r['success'] for r in result.values()):
                logger.warning(f"Diagnóstico guardado parcialmente para torre {data['id_torre']}")
            
            return {
                'success': True,
                'diagnostico': data,
                'storage_results': result
            }
        except Exception as e:
            logger.error(f"Error al guardar diagnóstico: {str(e)}", exc_info=True)
            raise
    
    
    @staticmethod
    def obtener_estado_general(id_torre: str) -> Dict:
        """Obtiene un resumen del estado tecnico de la torre"""
        try:
            diagnostico = DiagnosticoService.obtener_ultimo(id_torre)
            if not diagnostico:
                return {'estado': 'desconocido'}
            
            return {
                'estado': diagnostico['estado_general'],
                'bateria': diagnostico['nivel_bateria'],
                'ultima_conexion': diagnostico['tiempo_ultima_conexion'],
                'sensores': {
                    'temperatura': diagnostico['estado_sensor_temperatura'],
                    'humedad': diagnostico['estado_sensor_humedad']
                },
                'timestamp': diagnostico['timestamp']
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado general: {str(e)}")
            raise

