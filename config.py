"""
=============================================================================
NEXSTREAM — Configuración de la Aplicación
=============================================================================
Archivo: config.py
Descripción: Configuración multi-entorno usando clases Python.
             Soporta Development, Testing y Production.

Arquitectura:
    Config (base) → DevelopmentConfig
                  → TestingConfig
                  → ProductionConfig

Uso:
    from config import config
    app.config.from_object(config['development'])
=============================================================================
"""

import os
from datetime import timedelta
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """
    ─── Configuración Base ───────────────────────────────────────────────────
    Configuración compartida por todos los entornos.
    Las subclases heredan estos valores y pueden sobrescribirlos.
    """

    # ─── Seguridad ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nexstream-dev-key-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-dev-key'
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora

    # ─── Base de Datos ────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "instance" / "nexstream.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,    # Verificar conexión antes de usar
        'pool_recycle': 300,      # Reciclar conexiones cada 5 minutos
    }

    # ─── Sesiones ─────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_SECURE = False      # True en producción (HTTPS)
    SESSION_COOKIE_HTTPONLY = True     # No accesible desde JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'   # Protección CSRF básica
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False     # True en producción

    # ─── Subida de Archivos ────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 524288000))  # 500MB
    UPLOAD_FOLDER = BASE_DIR / 'app' / 'static' / 'uploads'
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mkv', 'avi', 'mov'}
    ALLOWED_SUBTITLE_EXTENSIONS = {'srt', 'vtt', 'ass', 'ssa'}
    MAX_IMAGE_SIZE = (2048, 2048)  # Máximo tamaño de imagen

    # ─── Email ────────────────────────────────────────────────────────────────
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'NEXSTREAM <noreply@nexstream.com>')

    # ─── Caché ────────────────────────────────────────────────────────────────
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_KEY_PREFIX = 'nexstream_'

    # ─── Compresión ───────────────────────────────────────────────────────────
    COMPRESS_REGISTER = True
    COMPRESS_LEVEL = 6           # Nivel de compresión gzip (1-9)
    COMPRESS_MIN_SIZE = 500      # Comprimir respuestas > 500 bytes

    # ─── Rate Limiting ────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_HEADERS_ENABLED = True  # Headers X-RateLimit-* en respuestas

    # ─── Plataforma ───────────────────────────────────────────────────────────
    PLATFORM_NAME = os.environ.get('PLATFORM_NAME', 'NEXSTREAM')
    PLATFORM_TAGLINE = os.environ.get('PLATFORM_TAGLINE', 'Tu universo de entretenimiento')
    PLATFORM_VERSION = '2.0.0'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@nexstream.com')

    # ─── Paginación ───────────────────────────────────────────────────────────
    ITEMS_PER_PAGE = 24           # Items por página en listados
    SEARCH_RESULTS_PER_PAGE = 20  # Resultados de búsqueda
    COMMENTS_PER_PAGE = 15        # Comentarios por página

    # ─── Tokens de Seguridad ──────────────────────────────────────────────────
    PASSWORD_RESET_EXPIRY = 3600   # 1 hora (segundos)
    EMAIL_CONFIRM_EXPIRY = 86400   # 24 horas (segundos)

    # ─── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL = 'INFO'
    LOG_FILE = BASE_DIR / 'logs' / 'nexstream.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB por archivo de log
    LOG_BACKUP_COUNT = 5               # Mantener 5 archivos de respaldo

    # ─── Pagos / Suscripciones (Stripe) ───────────────────────────────────────
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    @staticmethod
    def init_app(app):
        """
        Método llamado al inicializar la app con esta configuración.
        Crear directorios necesarios si no existen.
        """
        # Asegurar que existan los directorios necesarios
        upload_base = BASE_DIR / 'app' / 'static' / 'uploads'
        for subdir in ['covers', 'banners', 'avatars', 'thumbnails', 'videos']:
            (upload_base / subdir).mkdir(parents=True, exist_ok=True)

        # Asegurar directorio de logs
        (BASE_DIR / 'logs').mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """
    ─── Configuración de Desarrollo ─────────────────────────────────────────
    Optimizada para desarrollo local.
    - DEBUG activado
    - SQLite como base de datos
    - Sin SSL
    - Cache desactivado para ver cambios inmediatamente
    """

    DEBUG = True
    TESTING = False

    # Usar SQLite en desarrollo para facilidad
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "instance" / "nexstream.db"}'

    # Opciones extra para SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False},  # Solo SQLite
    }

    # Sin caché en desarrollo para ver cambios
    CACHE_TYPE = 'NullCache'

    # Mostrar queries SQL en consola
    SQLALCHEMY_ECHO = False  # Cambiar a True para depurar queries

    # Toolbar de debug
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = False

    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """
    ─── Configuración de Testing ────────────────────────────────────────────
    Optimizada para ejecución de pruebas.
    - Base de datos en memoria
    - CSRF desactivado para facilitar tests
    """

    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # Desactivar CSRF en tests

    # Base de datos en memoria para tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False},
    }

    CACHE_TYPE = 'NullCache'
    RATELIMIT_ENABLED = False  # Sin rate limiting en tests
    LOG_LEVEL = 'WARNING'


class ProductionConfig(Config):
    """
    ─── Configuración de Producción ─────────────────────────────────────────
    Optimizada para el servidor de producción.
    - PostgreSQL como base de datos
    - SSL/HTTPS obligatorio
    - Caché Redis
    - Rate limiting estricto
    """

    DEBUG = False
    TESTING = False

    # Seguridad de cookies en HTTPS
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    # PostgreSQL en producción
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Redis para caché en producción (recomendado)
    # CACHE_TYPE = 'RedisCache'
    # CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutos en producción

    # Rate limiting más estricto
    RATELIMIT_DEFAULT = '100 per day;30 per hour;5 per minute'

    LOG_LEVEL = 'WARNING'

    @classmethod
    def init_app(cls, app):
        """Configuración adicional para producción."""
        Config.init_app(app)

        # Configurar logging de producción hacia syslog
        import logging
        from logging.handlers import RotatingFileHandler

        # Handler de archivo con rotación
        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_BYTES,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(file_handler)


# ─── Mapa de Configuraciones ──────────────────────────────────────────────────
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,  # Configuración por defecto
}
