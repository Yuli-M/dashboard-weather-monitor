from api.database import engine
from api.models import (
    profiles,
    payments,
    torres,
    datos_meteorologicos,
    diagnostico_tecnico
)

from api.models.base import Base  # si tienes una base comun?

def crear_tablas():
    print("Creando tablas en SQLite...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")

if __name__ == "__main__":
    crear_tablas()
