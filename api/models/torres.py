# models/torre.py
from sqlalchemy import Column, Text, String, DateTime, JSON, ForeignKey
import uuid
from api.models.base import Base

class Torre(Base):
    __tablename__ = 'torres'

    id_torre = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(Text, nullable=False)
    ubicacion = Column(JSON, nullable=False)
    usuario_asignado = Column(String, ForeignKey('profiles.id'))
    estado = Column(Text)
    fecha_creacion = Column(DateTime)
    ultima_actualizacion = Column(DateTime)
    notas = Column(Text)
    origen_datos = Column(Text)

