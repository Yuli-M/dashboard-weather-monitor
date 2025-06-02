# models/datos_meteorologicos.py
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
import uuid
from api.models.base import Base

class DatoMeteorologico(Base):
    __tablename__ = 'datos_meteorologicos'

    id_dato = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_torre = Column(String, ForeignKey('torres.id_torre'))
    timestamp = Column(DateTime)
    temperatura = Column(Float)
    humedad_relativa = Column(Float)
    presion_atmosferica = Column(Float)
    velocidad_viento = Column(Float)
    direccion_viento = Column(Integer)
    precipitacion = Column(Float)
    radiacion_solar = Column(Float)
    indice_uv = Column(Integer)