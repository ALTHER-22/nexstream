"""
=============================================================================
NEXSTREAM — Extensiones de Flask
=============================================================================
Archivo: extensions.py
Descripción: Inicialización de todas las extensiones Flask.
             Se inicializan SIN la app (patrón Application Factory).
             La app se conecta después en create_app().

Patrón usado:
    1. Instanciar extensión aquí (sin app)
    2. Llamar extension.init_app(app) en create_app()

Esto permite múltiples instancias de la app (útil en tests).
=============================================================================
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ─── Base de Datos ────────────────────────────────────────────────────────────
# Instancia de SQLAlchemy — modelos importan 'db' de aquí
db = SQLAlchemy()

# Migraciones de base de datos con Alembic
migrate = Migrate()

# ─── Autenticación ────────────────────────────────────────────────────────────
# Gestión de sesiones de usuario
login_manager = LoginManager()
login_manager.login_view = 'auth.login'          # Vista de login
login_manager.login_message = 'Inicia sesión para acceder.'
login_manager.login_message_category = 'warning'
login_manager.session_protection = 'strong'      # Protección de sesión fuerte

# Hash de contraseñas con bcrypt
bcrypt = Bcrypt()

# ─── Seguridad ────────────────────────────────────────────────────────────────
# Protección CSRF en formularios
csrf = CSRFProtect()

# Rate Limiting — límite por IP del cliente
limiter = Limiter(
    key_func=get_remote_address,   # Limitar por IP
    default_limits=["200 per day", "50 per hour"],
    headers_enabled=True,          # Headers X-RateLimit en respuestas
    swallow_errors=True,           # No crashear si storage falla
)

# ─── Comunicación ─────────────────────────────────────────────────────────────
# Sistema de email para verificación y recuperación
mail = Mail()

# ─── Rendimiento ──────────────────────────────────────────────────────────────
# Caché de respuestas para vistas costosas
cache = Cache()

# Compresión gzip/brotli de respuestas HTTP
compress = Compress()
