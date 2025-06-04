# Sistema de Monitoreo Meteorológico - API Backend


Este proyecto proporciona una API completa para el monitoreo de estaciones meteorológicas, ofreciendo:

-  Registro y autenticación de usuarios
-  Recolección y almacenamiento de datos meteorológicos
-  Diagnósticos técnicos de las estaciones
-  Sistema de pagos 
-  Dashboard analítico

La arquitectura utiliza múltiples bases de datos para optimizar el rendimiento y garantizar disponibilidad incluso sin conexión.

---

##  Estructura del Proyecto

### Directorio Principal

| Carpeta/Archivo    | Descripción                                 |
|--------------------|---------------------------------------------|
| `api/`             | Núcleo de la aplicación Flask               |
| `config/`          | Configuraciones y variables de entorno      |
| `.env`             | Variables de entorno (no versionado)        |
| `requirements.txt` | Dependencias de Python                      |
| `run.py`           | Punto de entrada de la aplicación           |

###  API - Estructura Detallada

####  Models (Modelos de Datos)

| Archivo                      | Descripción                            |
|-----------------------------|----------------------------------------|
| `base.py`                   | Clase base para todos los modelos      |
| `torres.py`                 | Modelo de estaciones meteorológicas    |
| `datos_meteorologicos.py`  | Mediciones de sensores                 |
| `diagnostico_tecnico.py`   | Estado técnico de las torres           |
| `payments.py`               | Transacciones y suscripciones          |
| `profiles.py`               | Perfiles de usuario extendidos         |

####  Routes (Endpoints)

| Blueprint           | Descripción              | Endpoints Clave                                     |
|---------------------|--------------------------|-----------------------------------------------------|
| `auth_bp.py`        | Autenticación            | `/register`, `/login`, `/me`, `/logout`            |
| `torres_bp.py`      | Gestión de torres        | `GET /torres`, `POST /torres`, `GET /torres/<id>/data` |
| `dashboard_bp.py`   | Datos resumidos          | `GET /dashboard/user/<id>`                         |
| `estadisticas_bp.py`| Análisis meteorológico   | `GET /analytics/tower/<id>`                        |
| `payments_bp.py`    | Gestión de pagos         | `GET /payments`, `POST /payments`                  |
| `password_bp.py`    | Contraseñas              | `/reset-request`, `/reset`, `/update`              |

####  Services (Lógica de Negocio)

| Servicio                   | Responsabilidad                     |
|----------------------------|-------------------------------------|
| `auth_service.py`          | Lógica de autenticación             |
| `torre_service.py`         | Operaciones con torres              |
| `datos_service.py`         | Procesamiento de datos              |
| `diagnostico_service.py`   | Diagnósticos técnicos               |
| `payments_service.py`      | Procesamiento de pagos              |

#### Utils (Utilidades)

| Utilidad              | Función                                     |
|-----------------------|---------------------------------------------|
| `thread_manager.py`   | Hilos para simulación continua              |
| `simulator.py`        | Generación de datos simulados              |

---

##  Cómo Ejecutar el Proyecto

###  Prerrequisitos

- Python 3.9+
- Redis
- Cuenta en Supabase

###  Instalación

```bash
# 1. Clonar repositorio
git clone [repo_url]

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Ejecucion

```bash
# 1. Correr en modo desarrollo
python run.py
```


##  Tecnologías Clave

- **Flask**: Framework web ligero y rápido  
- **Supabase**: Backend como servicio (PostgreSQL + Auth)  
- **SQLAlchemy**: ORM para interacción con bases de datos  
- **Redis**: Almacenamiento en caché y Pub/Sub para alertas  
- **SQLite**: Almacenamiento local para modo offline  
- **Python threading**: Manejo de simulaciones concurrentes  

---

##  Notas de Desarrollo

- Todos los modelos heredan de `Base` desde `api/models/base.py`.
- Los datos horarios están normalizados a UTC.
- Las respuestas de la API siguen el siguiente formato:

```json
{
  "data": {},
  "meta": {},
  "error": null
}
```

##  Variables de Entorno Requeridas

Asegúrate de definir las siguientes variables en tu archivo `.env`:

```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_secret_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SQLITE_URL=sqlite://
REDIS_URL=redis://localhost:6379
```

##  Próximos Pasos

-  **Mejorar el sistema de alertas en tiempo real con Redis Pub/Sub**
- **Complemetar el export_service.py para que se coherente con la estructura actual y poder manejar archivos excel**
- **Opimizar el manejo de sesiones y la administracion de roles**
- **Incorporar el bot de telegram para consultar estado de las torres y recibir notificaciones en tiempo real**
- 





