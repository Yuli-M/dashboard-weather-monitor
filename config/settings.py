# # settings redis
# REDIS_HOST = "localhost"
# REDIS_PORT = 6379
# REDIS_DB = 0
# REDIS_PASSWORD = None  # ?


import os

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret-key-default')

    # SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLITE_URL', 'sqlite:///db.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
