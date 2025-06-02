# api/services/export_service.py
import csv
from io import StringIO
from datetime import datetime
from api.services import datos_service

class ExportService:
    @staticmethod
    def exportar_csv(id_torre: str, inicio: datetime, fin: datetime):
        datos = datos_service.obtener_rango_fechas(id_torre, inicio, fin)
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeceras
        writer.writerow([
            'timestamp', 'temperatura', 'humedad_relativa', 
            'presion_atmosferica', 'velocidad_viento'
        ])
        
        # Datos
        for dato in datos:
            writer.writerow([
                dato.timestamp.isoformat(),
                dato.temperatura,
                dato.humedad_relativa,
                dato.presion_atmosferica,
                dato.velocidad_viento
            ])
        
        output.seek(0)
        return output