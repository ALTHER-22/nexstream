"""
=============================================================================
NEXSTREAM — Decoradores de Autenticación y Autorización
=============================================================================
Archivo: app/utils/decorators.py
Descripción: Decoradores para proteger rutas según roles y permisos.

Decoradores disponibles:
  @admin_required        — Solo administradores
  @moderator_required    — Moderadores y admins
  @verified_required     — Solo cuentas verificadas
  @anonymous_required    — Solo usuarios NO autenticados (login/registro)
  @rate_limit_login      — Rate limit específico para login
=============================================================================
"""

from functools import wraps
from flask import abort, redirect, url_for, flash, request, jsonify
from flask_login import current_user


def admin_required(f):
    """
    Decorador: Requiere que el usuario sea administrador.
    Si no lo es, devuelve 403 Forbidden.

    Uso:
        @bp.route('/admin/panel')
        @login_required
        @admin_required
        def panel():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            # Si es petición AJAX, devolver JSON
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Acceso denegado', 'code': 403}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def moderator_required(f):
    """
    Decorador: Requiere que el usuario sea moderador o admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_moderator:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Acceso denegado', 'code': 403}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def verified_required(f):
    """
    Decorador: Requiere que la cuenta esté verificada por email.
    Redirige a una página de aviso si no está verificada.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_verified:
            flash('Por favor verifica tu cuenta antes de continuar.', 'warning')
            return redirect(url_for('auth.resend_verification'))
        return f(*args, **kwargs)
    return decorated_function


def anonymous_required(f):
    """
    Decorador: Solo para usuarios NO autenticados.
    Redirige al inicio si ya está logueado (para login/registro).

    Uso:
        @bp.route('/login')
        @anonymous_required
        def login():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """
    Decorador para endpoints de API que requieren autenticación.
    Devuelve JSON en lugar de redirigir.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Autenticación requerida',
                'code': 401,
            }), 401
        return f(*args, **kwargs)
    return decorated_function
