from flask import Flask, g, request, jsonify
from sqlalchemy import text
from config.settings import Config
from api.database import storage_manager, sincronizar_datos_iniciales, db_manager
from api.models.torres import Torre
from api.utils.thread_manager import thread_manager
import logging
from logging.handlers import RotatingFileHandler
import atexit
from flask_cors import CORS 

from api.routes import(
    auth_bp,
    dashboard_bp,
    estadisticas_bp,
    payments_bp,
    torres_bp,
    password_bp
)


logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # configuracion CORS 
    CORS(app, resources={
             r"/api/*": {
                 "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True,
                 "expose_headers": ["Content-Type"],
                 "max_age": 600
             }
         })


    # configuracion de logging
    configure_logging(app)

    # inicialización de la base de datos
    with app.app_context():
        init_database()
        sincronizar_datos_iniciales() 
        # init_services()
        try:
           with db_manager.get_session() as session:
                if session.query(Torre).count() == 0:
                    logger.warning("No hay torres en la base de datos")
                else:
                    thread_manager.iniciar_simulaciones()
                        
        except Exception as e:
            logger.critical(f"Error durante inicialización: {str(e)}")
            raise
    
        # try:
        #     thread_manager.iniciar_simulaciones()
        #     app.logger.info("Simulaciones de torres iniciadas")
        # except Exception as e:
        #     app.logger.error(f"Error al iniciar simulaciones: {str(e)}")


    # Registrar blueprints (rutas)
    register_blueprints(app)


    # Manejo de inicio/parada
    # @app.before_request
    # def startup_operations():

    # Manejo explicito de OPTIONS para todas las rutas
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            return response
            

    @atexit.register
    def shutdown_operations():
        """Operaciones al detener la aplicación"""
        try:
            thread_manager.detener_simulaciones()
            app.logger.info("Simulaciones de torres detenidas")
        except Exception as e:
            app.logger.error(f"Error al detener simulaciones: {str(e)}")

    return app

def configure_logging(app):
    """Configura el sistema de logging"""
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    
    # Log a archivo
    file_handler = RotatingFileHandler('meteorological_monitor.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # tambien mostrar logs en consola en desarrollo
    if app.config['DEBUG']:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        app.logger.addHandler(stream_handler)

def init_database():
    """Inicializa y verifica las conexiones a bases de datos"""
    try:
        # verificar conexion a SQLite
        with db_manager.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # a Supabase
        db_manager.supabase.table("torres").select("id_torre").limit(1).execute()
        
        # a Redis
        db_manager.redis.ping()
        
        logging.info("Conexiones a bases de datos verificadas")
    except Exception as e:
        logging.error(f"Error en conexiones a bases de datos: {str(e)}")
        raise

# def init_services():
#     """Inicializar servicios adicionales"""
#     # inicializar otros servicios ?
#     pass

def register_blueprints(app):
    """Registra los blueprints de la aplicación"""
    from api.routes import torres_bp, auth_bp, dashboard_bp, estadisticas_bp, payments_bp, password_bp  # importar blueprints
    
    blueprints = [
        {'bp': torres_bp.torres_bp, 'url_prefix': '/api/torres'},
        {'bp': auth_bp.auth_bp, 'url_prefix': '/api/auth'},
        {'bp': estadisticas_bp.estadisticas_bp, 'url_prefix': '/api/analytics'},
        {'bp': dashboard_bp.dashboard_bp, 'url_prefix': '/api/dashboard'},
        {'bp': payments_bp.payments_bp, 'url_prefix': '/api/payments'},
        {'bp': password_bp.password_bp, 'url_prefix': '/api/password'}
    ]

    for bp in blueprints:
        app.register_blueprint(bp['bp'], url_prefix=bp['url_prefix'])
        app.logger.info(f"Blueprint registrado: {bp['bp'].name}")

# crear la aplicacion Flask
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)