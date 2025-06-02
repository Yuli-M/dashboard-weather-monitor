# models/diagnostico_tecnico.py
from sqlalchemy import Column, Float, String, DateTime, ForeignKey, Text
import uuid
from api.models.base import Base
from datetime import datetime

class DiagnosticoTecnico(Base):
    __tablename__ = 'diagnosticos_tecnicos'

    id_diagnostico = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_torre = Column(String, ForeignKey('torres.id_torre'))
    timestamp = Column(DateTime)
    nivel_bateria = Column(Float)
    tiempo_ultima_conexion = Column(DateTime)
    estado_sensor_temperatura = Column(Text)
    estado_sensor_humedad = Column(Text)
    estado_general = Column(Text)
