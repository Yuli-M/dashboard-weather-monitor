# api/services/notificacion_service.py
from typing import List
from api.models.diagnostico_tecnico import DiagnosticoTecnico

class NotificacionService:
    @staticmethod
    def verificar_alertas(diagnosticos: List[DiagnosticoTecnico]):
        alertas = []
        for diag in diagnosticos:
            if diag.estado_general == 'Crítico':
                alertas.append({
                    'id_torre': diag.id_torre,
                    'mensaje': f'Alerta crítica en torre {diag.id_torre}',
                    'timestamp': diag.timestamp
                })
            elif diag.estado_general == 'Alerta':
                alertas.append({
                    'id_torre': diag.id_torre,
                    'mensaje': f'Alerta en torre {diag.id_torre}',
                    'timestamp': diag.timestamp
                })
        return alertas