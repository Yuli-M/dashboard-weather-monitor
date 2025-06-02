from api.database import db_manager
from datetime import datetime, timedelta
import logging
from sqlalchemy import inspect
from sqlalchemy import text

# configuracion basica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mostrar_resumen_completo():
    """Muestra comparativa detallada de todas las tablas"""
    try:
        # configurar conexion
        engine = db_manager.engine
        
        # lista de todas las tablas en SQLite
        inspector = inspect(engine)
        tablas_sqlite = inspector.get_table_names()
        
        # tablas a comparar
        tablas_comunes = [
            'torres',
            'profiles',
            'payments',
            'datos_meteorologicos', 
            'diagnostico_tecnico'
        ]
        
        resultados = []
        
        for tabla in tablas_comunes:
            if tabla not in tablas_sqlite:
                logger.warning(f"Tabla {tabla} no existe en SQLite")
                continue
                
            # conteo en SQLite
            with db_manager.get_session() as session:
                count_sqlite = session.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
            
            # conteo en Supabase
            try:
                res = db_manager.supabase.table(tabla).select('*', count='exact').execute()
                count_supabase = res.count
            except Exception as e:
                logger.error(f"Error consultando {tabla} en Supabase: {str(e)}")
                count_supabase = "Error"
            
            resultados.append([
                tabla,
                count_sqlite,
                count_supabase,
                count_sqlite - count_supabase if isinstance(count_supabase, int) else "N/A"
            ])
        
        # mostrar resultados
        print("\nCOMPARATIVO DE BASES DE DATOS")
        print("-" * 50)
        for resultado in resultados:
            print(f"{resultado[0]}: SQLite={resultado[1]} | Supabase={resultado[2]} | Diferencia={resultado[3]}")
        
    except Exception as e:
        logger.error(f"Error generando resumen: {str(e)}")

if __name__ == "__main__":
    mostrar_resumen_completo()