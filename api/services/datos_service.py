# api/services/datos_service.py
from api.database import storage_manager, db_manager
from api.models.datos_meteorologicos import DatoMeteorologico
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

# api/services/datos_service.py
class DatosService:
    @staticmethod
    def obtener_ultimos(id_torre: str, horas: int = 24) -> List[Dict]:
        """Obtiene datos meteorológicos de una torre con estrategia de caché inteligente"""
        try:
            # primero verificar Redis (ultimos datos)
            redis_key = f"torre:{id_torre}:last_data"
            cached_data = db_manager.redis.get(redis_key)
            if cached_data:
                return [json.loads(cached_data)]

            # 2.consultar Supabase (datos historicos)
            response = db_manager.supabase.table('datos_meteorologicos').select('*').eq('id_torre', id_torre) \
                .gte('timestamp', (datetime.utcnow() - timedelta(hours=horas)).isoformat()).order('timestamp', desc=True) \
                .limit(100).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error obteniendo datos: {str(e)}")
            raise

    @staticmethod
    def calcular_estadisticas(id_torre: str, horas: int = 24) -> Dict:
        """Calcula estadísticas avanzadas para una torre"""
        try:
            datos = DatosService.obtener_ultimos(id_torre, horas)
            if not datos:
                return {}

            #extraer series temporales
            temps = [d['temperatura'] for d in datos if d.get('temperatura') is not None]
            humedades = [d['humedad_relativa'] for d in datos if d.get('humedad_relativa') is not None]
            vientos = [d['velocidad_viento'] for d in datos if d.get('velocidad_viento') is not None]

            #Calculos basicos
            stats = {
                "temperatura": {
                    "max": max(temps) if temps else None,
                    "min": min(temps) if temps else None,
                    "promedio": sum(temps)/len(temps) if temps else None,
                    "unidad": "°C"
                },
                "humedad": {
                    "max": max(humedades) if humedades else None,
                    "min": min(humedades) if humedades else None,
                    "promedio": sum(humedades)/len(humedades) if humedades else None,
                    "unidad": "%"
                },
                "viento": {
                    "max": max(vientos) if vientos else None,
                    "promedio": sum(vientos)/len(vientos) if vientos else None,
                    "unidad": "km/h"
                },
                "muestras": len(datos),
                "desde": datos[-1]['timestamp'] if datos else None,
                "hasta": datos[0]['timestamp'] if datos else None
            }

            # Guardar en cache
            try:
                db_manager.redis.set(
                    f"stats:{id_torre}:{horas}h",
                    json.dumps(stats),
                    ex=3600  # expira en 1 h
                )
            except Exception as e:
                logger.warning(f"No se pudo cachear stats: {str(e)}")

            return stats

        except Exception as e:
            logger.error(f"Error calculando estadísticas: {str(e)}")
            raise

    @staticmethod
    def obtener_diagnostico(id_torre: str) -> Optional[Dict]:
        """Obtiene el ultimo diagnostico tecnico de la torre"""
        try:
            response = db_manager.supabase.table('diagnostico_tecnico').select('*').eq('id_torre', id_torre) \
                .order('timestamp', desc=True).limit(1).execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error obteniendo diagnostico: {str(e)}")
            raise