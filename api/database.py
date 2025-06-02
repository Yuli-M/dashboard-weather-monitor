import os
import json
import logging
from typing import Dict, List, Generator, Optional
from contextlib import contextmanager
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import SQLAlchemyError
from supabase import create_client, Client
from supabase.client import ClientOptions
import time
from datetime import datetime
import redis
from dateutil.parser import parse

logger = logging.getLogger(__name__)
load_dotenv()

@dataclass
class DatabaseConfig:
    supabase_url: str
    supabase_key: str #??
    sqlite_url: str = "sqlite:///db.sqlite3"
    redis_url: str = "redis://localhost:6379/0"

class DatabaseManager:
    """
    Gestiona todas las conexiones a bases de datos usando el patrón Singleton.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicialización perezosa de conexiones con manejo de errores"""
        config = DatabaseConfig(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY"),#??
            sqlite_url=os.getenv("SQLITE_URL", "sqlite:///db.sqlite3"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )

        try:
            #configurar SQLite
            self.engine = create_engine(
                config.sqlite_url,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True
            )

            #crear sesion
            self.SessionLocal = scoped_session(
                sessionmaker(
                    bind=self.engine,
                    autocommit=False,
                    autoflush=False,
                )
            )

            # configurar Supabase
            self.supabase = create_client(
                config.supabase_url,
                config.supabase_key,
                options=ClientOptions(
                    postgrest_client_timeout=15,
                    storage_client_timeout=15,
                    schema="public",
                    auto_refresh_token=False,
                    persist_session=False,#?
                    #  headers={
                    #     "Authorization": f"Bearer {config.supabase_key}",
                    #     "apikey": config.supabase_key
                    # }
                    
                )
            )
            
            # configurar Redis
            self.redis = redis.Redis.from_url(
                config.redis_url,
                socket_connect_timeout=5,
                health_check_interval=30,
                decode_responses=False,
            )
            

            self._verify_connections()
            
            # inicializar estructura local
            self._init_local_cache()
            
            logger.info("DatabaseManager inicializado correctamente")
            
        except Exception as e:
            logger.critical(f"Error inicializando DatabaseManager: {str(e)}")
            raise

    def _verify_connections(self):
        """Verifica que todas las conexiones estén activas"""
        # Redis
        if not self.redis.ping():
            raise ConnectionError("No se pudo conectar a Redis")
        
        # SQLite
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as e:
            raise ConnectionError(f"Error conectando a SQLite: {str(e)}")
        
        # Supabase
        try:
            res = self.supabase.table('torres').select('id_torre').limit(1).execute()
            if not res.data:
                logger.warning("Tabla 'torres' en Supabase está vacía")
        except Exception as e:
            raise ConnectionError(f"Error conectando a Supabase: {str(e)}")

    def _init_local_cache(self):
        """Inicializa la estructura de la base de datos local"""
        from api.models.base import Base
        Base.metadata.create_all(bind=self.engine)
        logger.info("Estructura de SQLite verificada")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Provee una sesión de base de datos con manejo automático de transacciones.
        
        Ejemplo:
        with db_manager.get_session() as session:
            session.query(...)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

class StorageManager:
    """
    Gestiona el almacenamiento distribuido entre Supabase (principal), 
    SQLite (caché local) y Redis (caché temporal).
    """
    MODEL_MAPPING = {
        'meteorologico': ('datos_meteorologicos', 'DatoMeteorologico'),
        'diagnostico': ('diagnostico_tecnico', 'DiagnosticoTecnico')
    }


    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _convert_dates(self, data: dict) -> dict:
        """Convierte strings de fecha a objetos datetime para SQLite"""
        converted = data.copy()
        for key, value in converted.items():
            if isinstance(value, str):
                try:
                    converted[key] = parse(value)
                except (ValueError, TypeError):
                    pass
        return converted

    def _prepare_for_supabase(self, data: dict) -> dict:
        """Convierte objetos datetime a strings ISO para Supabase"""
        prepared = data.copy()
        for key, value in prepared.items():
            if isinstance(value, datetime):
                prepared[key] = value.isoformat()
        return prepared

    def save(self, data_type: str, data: Dict) -> Dict:
        if data_type not in self.MODEL_MAPPING:
            raise ValueError(f"Tipo de dato no soportado: {data_type}")

        table_name, model_name = self.MODEL_MAPPING[data_type]
        
        try:
            #importar modelo dinamicamente
            model_module = __import__(f'api.models.{table_name}', fromlist=[model_name])
            model_class = getattr(model_module, model_name)
            
            # validar y convertir datos
            instance = model_class(**data)
            
            results = {
                'supabase': self._save_to_supabase(table_name, data),
                'sqlite': self._save_to_sqlite(model_class, data),
                'redis': {'success': True}  # solo para datos meteorologicos ?
            }
            
            if data_type == 'meteorologico':
                results['redis'] = self._save_to_redis(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error guardando {data_type}: {str(e)}")
            raise

    def _save_to_supabase(self, table_name: str, data: Dict) -> Dict:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                prepared_data = self._prepare_for_supabase(data) 
                res = self.db.supabase.table(table_name).insert(prepared_data).execute()
                return {'success': True, 'data': res.data[0] if res.data else None}
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error en Supabase (intento {attempt + 1}): {str(e)}")
                    return {'success': False, 'error': str(e)}
                time.sleep(1)

    def _save_to_sqlite(self, model_class, data: Dict) -> Dict:
        try:
            converted_data = self._convert_dates(data) 
            with self.db.get_session() as session:
                instance = model_class(**converted_data)
                session.add(instance)
                session.commit()
                return {'success': True, 'id ?': str(instance)}
        except Exception as e:
            logger.error(f"Error en SQLite: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _save_to_redis(self, data: Dict) -> Dict:
        try:
            prepared_data = self._prepare_for_supabase(data) #JSON?
            serialized = json.dumps(prepared_data, default=str)  #maneja datetime
            self.db.redis.set(
                f"torre:{data['id_torre']}:last_data",
                serialized,
                ex=3600 # una hora de expiracion
            )
            return {'success': True}
        except Exception as e:
            logger.error(f"Error en Redis: {str(e)}")
            return {'success': False, 'error': str(e)}


def sincronizar_datos_iniciales():
    """Sincroniza todos los datos iniciales desde Supabase"""
    sincronizar_tabla('torres')
    sincronizar_tabla('profiles')
    sincronizar_tabla('payments')

def sincronizar_tabla(tabla: str):
    """Sincroniza una tabla específica desde Supabase a SQLite"""
    db_manager = DatabaseManager()
    
    try:
        # datos de Supabase
        response = db_manager.supabase.table(tabla).select('*').execute()
        datos_supabase = response.data
        
        if not datos_supabase:
            logger.warning(f"Tabla '{tabla}' en Supabase esta vacia")
            return

        MODEL_NAMES ={
            'profiles': 'Profile',
            'torres': 'Torre',
            'payments': 'Payment',
            'diagnostico_tecnico': 'DiagnosticoTecnico',
            'datos_meteorologicos': 'DatoMeteorologico'
        }

        if tabla not in MODEL_NAMES:
            raise ValueError(f"No existe mapeo para la tabla {tabla}")
        
        # importar dinamicamente el modelo correcto
        model_module = __import__(f'api.models.{tabla}', fromlist=[MODEL_NAMES[tabla]])
        model_class = getattr(model_module, MODEL_NAMES[tabla])


        # Sincronizar con SQLite
        with db_manager.get_session() as session:


            # obtener el id dinamicamente
            primary_key = next(col.name for col in model_class.__table__.primary_key.columns)

            # Obtener IDs existentes
            # existing_ids = {t[0] for t in session.query(model_class.id).all()}
            existing_ids = {t[0] for t in session.query(getattr(model_class, primary_key)).all()}
            
            nuevos = 0
            actualizados = 0
            
            ###
            for item in datos_supabase:
                item_id = item.get('id') or item.get('id_torre') or item.get('id_diagnostico') or item.get('id_dato')

                # # Convertir strings de fecha a objetos datetime
                # if 'updated_at' in item and isinstance(item['updated_at'], str):
                #     try:
                #         item['updated_at'] = parse(item['updated_at'])
                #     except (ValueError, TypeError) as e:
                #         logger.warning(f"Error parseando fecha en {tabla} ID {item.get('id')}: {e}")
                #         item['updated_at'] = None  # O usa datetime.now() como fallback

                 #  strings de supabase fecha a objetos datetime
                for field in ['fecha_creacion', 'ultima_actualizacion', 'updated_at', 'expires_at','payment_date' ]:  # A;ade todos los campos de fecha
                    if field in item and item[field] and isinstance(item[field], str):
                        try:
                            item[field] = parse(item[field])
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error parseando fecha en {tabla} ID {item.get('id')}: {e}")
                            item[field] = datetime.now()  #
                
                if item_id in existing_ids:
                    session.query(model_class).filter_by(**{primary_key: item_id}).update(item)
                    actualizados += 1
                else:
                    session.add(model_class(**item)) #item
                    nuevos += 1
            
            session.commit()
            logger.info(
                f"Sincronización de {tabla}: {nuevos} nuevos, "
                f"{actualizados} actualizados"
            )
            
    except Exception as e:
        logger.error(f"Error sincronizando {tabla}: {str(e)}")
        raise

# Inicializacion global
db_manager = DatabaseManager()
storage_manager = StorageManager(db_manager)