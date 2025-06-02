import threading
import time
import logging
import json
from datetime import datetime
from typing import Dict

from api.database import storage_manager, db_manager
from api.utils.simulator import generar_datos_meteorologicos, generar_diagnostico_tecnico

logger = logging.getLogger(__name__)

class ThreadManager:
    _instance = None
    _lock = threading.Lock()
    active_threads: Dict[str, threading.Thread] 
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.active_threads = {}
                cls._instance._running = True
        return cls._instance
    
    def iniciar_hilo_torre(self, torre: Dict):
        """Inicia un hilo de simulación para una torre"""
        id_torre = torre["id_torre"]
        
        if id_torre in self.active_threads:
            logger.warning(f"La torre {id_torre} ya tiene un hilo activo")
            return
        
        def hilo_torre():
            """Hilo de simulación para una torre individual"""
            logger.info(f"Iniciando simulación para torre {id_torre}")
            
            while getattr(self, '_running', True):
                try:
                    # generar datos simulados
                    datos_meteo = {
                        **generar_datos_meteorologicos(id_torre),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    diagnostico = {
                        **generar_diagnostico_tecnico(id_torre),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    required_meteo = ['id_torre', 'temperatura', 'humedad_relativa']
                    required_diag = ['id_torre', 'nivel_bateria', 'estado_general']
                    
                    if not all(k in datos_meteo for k in required_meteo):
                        raise ValueError(f"Faltan campos meteorológicos requeridos: {required_meteo}")
                        
                    if not all(k in diagnostico for k in required_diag):
                        raise ValueError(f"Faltan campos de diagnóstico requeridos: {required_diag}")

                    #guardar usando storage_manager (adaptado a Supabase)
                    resultado_meteo = storage_manager.save('meteorologico', datos_meteo)
                    resultado_diag = storage_manager.save('diagnostico', diagnostico)
                    
                    logger.info(f"Datos guardados para {id_torre} | "
                            f"Meteo: {resultado_meteo.get('supabase', {}).get('success')} | "
                            f"Diag: {resultado_diag.get('supabase', {}).get('success')}")
                    
                    #verificar alertas
                    self._verificar_alertas(
                        datos_meteo,
                        diagnostico,
                        umbrales={
                            'temperatura_alta': 35,
                            'temperatura_baja': 5,
                            'humedad_alta': 90,
                            'bateria_baja': 20
                        }
                    )
                    
                    time.sleep(10)  #intervalo configurable
                    
                except Exception as e:
                    logger.error(f"Error en simulación torre {id_torre}: {str(e)}", exc_info=True)
                    time.sleep(30)  # backoff en caso de error / esperar antes de reintentar

        thread = threading.Thread(
            target=hilo_torre,
            daemon=True,
            name=f"torre_sim_{id_torre}"
        )
        self.active_threads[id_torre] = thread
        thread.start()
    
    def iniciar_simulaciones(self):
        """Inicia hilos para todas las torres activas"""
        logger.info("Iniciando simulaciones para torres activas")
        
        try:
            # usar storage_manager.supabase en lugar de supabase directo (?)
            torres_activas = db_manager.supabase.table("torres").select("id_torre").eq("estado", "Activa").not_.is_("usuario_asignado", "null").execute().data
            
            for torre in torres_activas:
                self.iniciar_hilo_torre(torre)
            
            logger.info(f"Simulación iniciada para {len(torres_activas)} torres")
            
        except Exception as e:
            logger.error(f"Error al iniciar simulaciones: {str(e)}")
    
    def detener_simulaciones(self):
        """Detiene todos los hilos de simulación"""
        self._running = False
        for thread in self.active_threads.values():
            thread.join(timeout=5)
        self.active_threads.clear()
        logger.info("Todas las simulaciones han sido detenidas")

    def _verificar_alertas(self, datos: dict, diagnostico: dict, umbrales: dict):
        """Verifica condiciones de alerta con umbrales configurables"""
        alertas = []
        
        # Alertas meteorológicas
        temp = datos.get('temperatura')
        if temp > umbrales['temperatura_alta']:
            alertas.append(f"Temperatura alta: {temp}°C")
        elif temp < umbrales['temperatura_baja']:
            alertas.append(f"Temperatura baja: {temp}°C")
        
        if datos.get('humedad_relativa', 0) > umbrales['humedad_alta']:
            alertas.append(f"Humedad alta: {datos['humedad_relativa']}%")
        
        # Alertas técnicas
        if diagnostico.get('nivel_bateria', 100) < umbrales['bateria_baja']:
            alertas.append(f"Batería crítica: {diagnostico['nivel_bateria']}%")
        
        if diagnostico.get('estado_general') == 'Crítico':
            alertas.append("Estado CRÍTICO de la torre")
        
        # publicar si hay alertas  ?
        if alertas:
            self._publicar_alerta(
                datos['id_torre'],
                alertas,
                datos=datos,
                diagnostico=diagnostico
            )


    def _publicar_alerta(self, id_torre: str, alertas: list, datos: dict, diagnostico: dict):
        """Publica alertas en Redis"""
        try:
            mensaje = {
                'id_torre': id_torre,
                'timestamp': datetime.utcnow().isoformat(),
                'alertas': alertas,
                'datos': datos,
                'diagnostico': diagnostico
            }
            
            db_manager.redis.publish(
                f"alertas:{id_torre}",
                json.dumps(mensaje)
            )
            
            logger.warning(f"Alerta para torre {id_torre}: {', '.join(alertas)}")
        except Exception as e:
            logger.error(f"Error publicando alerta: {str(e)}")

# Singleton global
thread_manager = ThreadManager()