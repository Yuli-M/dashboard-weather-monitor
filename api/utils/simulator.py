import random
from datetime import datetime, timedelta
from typing import Dict, Literal

def generar_datos_meteorologicos(id_torre: str) -> dict:
    return {
        "id_torre": id_torre,
        "timestamp": datetime.utcnow().isoformat(),
        "temperatura": round(random.uniform(10.0, 35.0), 2),
        "humedad_relativa": round(random.uniform(30.0, 90.0), 2),
        "presion_atmosferica": round(random.uniform(950.0, 1050.0), 2),
        "velocidad_viento": round(random.uniform(0.0, 20.0), 2),
        "direccion_viento": random.randint(0, 360),
        "precipitacion": round(random.uniform(0.0, 10.0), 2),
        "radiacion_solar": round(random.uniform(100.0, 1000.0), 2),
        "indice_uv": random.randint(0, 11),
    }

def generar_diagnostico_tecnico(id_torre: str) -> dict:
    nivel_bateria = round(random.uniform(10.0, 100.0), 2)
    tiempo_ultima_conexion = datetime.utcnow() - timedelta(minutes=random.randint(1, 30))

    estado_sensor_temperatura = random.choices(["OK", "Error"], weights=[0.95, 0.05])[0]
    estado_sensor_humedad = random.choices(["OK", "Error"], weights=[0.95, 0.05])[0]
    estado_general = "Normal"

    if nivel_bateria < 20.0 or "Error" in (estado_sensor_temperatura, estado_sensor_humedad):
        estado_general = random.choices(["Alerta", "Crítico"], weights=[0.7, 0.3])[0]

    return {
        "id_torre": id_torre,
        "timestamp": datetime.utcnow().isoformat(),
        "nivel_bateria": nivel_bateria,
        "tiempo_ultima_conexion": tiempo_ultima_conexion,
        "estado_sensor_temperatura": estado_sensor_temperatura,
        "estado_sensor_humedad": estado_sensor_humedad,
        "estado_general": estado_general,
    }
