"""
=============================================================================
NEXSTREAM — Application Factory (create_app)
=============================================================================
Archivo: app/__init__.py
Descripción: Fábrica de la aplicación Flask.
             Usa el patrón Application Factory para máxima flexibilidad.

Ventajas del patrón:
    - Múltiples instancias (tests, producción, staging)
    - Configuración dinámica
    - Evita importaciones circulares
    - Facilita testing unitario

Flujo:
    1. Crear instancia Flask
    2. Cargar configuración
    3. Inicializar extensiones
    4. Registrar blueprints
    5. Registrar manejadores de errores
    6. Registrar context processors (variables globales en templates)
    7. Configurar logging
=============================================================================
"""

import os
from dotenv import load_dotenv
load_dotenv()

import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, g
from config import config

# Importar todas las extensiones (inicializadas sin app)
from extensions import db, migrate, login_manager, bcrypt, csrf, mail, cache, compress, limiter


def create_app(config_name: str = None) -> Flask:
    """
    ─── Fábrica de la Aplicación ─────────────────────────────────────────────
    Crea y configura la instancia de Flask.

    Args:
        config_name: Nombre de la configuración ('development', 'production', 'testing')
                     Si no se especifica, usa la variable de entorno FLASK_ENV
                     o 'development' por defecto.

    Returns:
        Flask: Instancia configurada de la aplicación.
    """
    # Determinar configuración a usar
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # ─── Crear Instancia Flask ─────────────────────────────────────────────────
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static',
    )

    # ─── Cargar Configuración ──────────────────────────────────────────────────
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)  # Inicialización específica del entorno

    # ─── Inicializar Extensiones ───────────────────────────────────────────────
    _init_extensions(app)

    # ─── Registrar Blueprints ──────────────────────────────────────────────────
    _register_blueprints(app)

    # ─── Manejadores de Errores ────────────────────────────────────────────────
    _register_error_handlers(app)

    # ─── Context Processors ───────────────────────────────────────────────────
    _register_context_processors(app)

    # ─── Shell Context ────────────────────────────────────────────────────────
    _register_shell_context(app)

    # ─── Logging ──────────────────────────────────────────────────────────────
    _configure_logging(app)

    app.logger.info(f'🚀 NEXSTREAM iniciado en modo: {config_name}')

    return app


def _init_extensions(app: Flask) -> None:
    """
    ─── Inicializar Extensiones ──────────────────────────────────────────────
    Conecta cada extensión con la instancia de la app.
    Orden importante: db primero, luego login_manager, etc.
    """
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    limiter.init_app(app)

    # Configurar Flask-Login: función que carga el usuario desde la sesión
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        """Carga el usuario por ID desde la base de datos."""
        return User.query.get(int(user_id))


def _register_blueprints(app: Flask) -> None:
    """
    ─── Registrar Blueprints ─────────────────────────────────────────────────
    Cada módulo es un Blueprint independiente.
    Esto permite desarrollo modular y desacoplado.
    """

    # Blueprint principal (página de inicio, catálogo)
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Blueprint de autenticación (login, registro, etc.)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Blueprint de administración
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Blueprint de API REST (para AJAX y futuras integraciones)
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Blueprint de usuario (perfil, historial, favoritos)
    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/perfil')

    # Blueprint de suscripciones y pagos (Stripe)
    from app.subscription import bp as subscription_bp
    app.register_blueprint(subscription_bp, url_prefix='/suscripcion')


def _register_error_handlers(app: Flask) -> None:
    """
    ─── Manejadores de Errores ───────────────────────────────────────────────
    Páginas de error personalizadas y elegantes.
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Error 400: Petición inválida."""
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Error 401: No autorizado."""
        return render_template('errors/401.html', error=error), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Error 403: Acceso prohibido."""
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        """Error 404: Página no encontrada."""
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        """Error 429: Demasiadas peticiones (rate limit)."""
        return render_template('errors/429.html', error=error), 429

    @app.errorhandler(500)
    def internal_error(error):
        """Error 500: Error interno del servidor."""
        db.session.rollback()  # Revertir transacción pendiente
        return render_template('errors/500.html', error=error), 500


def _register_context_processors(app: Flask) -> None:
    """
    ─── Context Processors ───────────────────────────────────────────────────
    Variables disponibles globalmente en TODOS los templates Jinja2.
    Se ejecutan en cada petición.
    """

    @app.context_processor
    def inject_platform_info():
        """Inyectar información de la plataforma en templates."""
        return {
            'platform_name': app.config.get('PLATFORM_NAME', 'NEXSTREAM'),
            'platform_tagline': app.config.get('PLATFORM_TAGLINE', ''),
            'platform_version': app.config.get('PLATFORM_VERSION', '2.0.0'),
        }

    @app.context_processor
    @cache.cached(timeout=3600, key_prefix='categories_nav')
    def inject_categories():
        """Inyectar categorías disponibles para la navegación."""
        try:
            from app.models.content import Category
            categories = Category.query.filter_by(is_active=True).order_by(Category.order).limit(10).all()
            return {'nav_categories': categories}
        except Exception:
            return {'nav_categories': []}

    @app.context_processor
    def inject_theme():
        """Inyectar tema actual del usuario (dark/light)."""
        from flask_login import current_user
        theme = 'dark'  # Tema por defecto
        if hasattr(current_user, 'theme') and current_user.is_authenticated:
            theme = current_user.theme or 'dark'
        return {'current_theme': theme}

    @app.context_processor
    def inject_utilities():
        """Inyectar funciones de utilidad para templates."""
        import datetime
        return {
            'current_year': datetime.datetime.now().year,
            'now': datetime.datetime.now(),
        }


def _register_shell_context(app: Flask) -> None:
    """
    ─── Shell Context ────────────────────────────────────────────────────────
    Hace que los modelos estén disponibles en 'flask shell' sin importarlos.
    Útil para pruebas rápidas en consola.
    """

    @app.shell_context_processor
    def make_shell_context():
        from app.models.user import User, Role
        from app.models.content import Series, Movie, Season, Episode, Category
        from app.models.interaction import Favorite, WatchHistory, Comment, Rating
        return {
            'db': db,
            'User': User,
            'Role': Role,
            'Series': Series,
            'Movie': Movie,
            'Season': Season,
            'Episode': Episode,
            'Category': Category,
            'Favorite': Favorite,
            'WatchHistory': WatchHistory,
            'Comment': Comment,
            'Rating': Rating,
        }


def _configure_logging(app: Flask) -> None:
    """
    ─── Configuración de Logging ─────────────────────────────────────────────
    Configura el sistema de logs según el entorno.
    En producción: archivo con rotación.
    En desarrollo: consola con formato detallado.
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))

    if not app.debug and not app.testing:
        # Logging a archivo en producción/staging
        log_file = app.config.get('LOG_FILE')
        if log_file:
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=app.config.get('LOG_MAX_BYTES', 10485760),
                backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            app.logger.addHandler(file_handler)
    else:
        # Logging a consola en desarrollo
        logging.basicConfig(
            level=log_level,
            format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )

    app.logger.setLevel(log_level)
