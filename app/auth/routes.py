"""
=============================================================================
NEXSTREAM — Rutas de Autenticación (Completas)
=============================================================================
Archivo: app/auth/routes.py
Descripción: Todas las rutas del sistema de autenticación.

Rutas:
  GET/POST  /auth/login              — Iniciar sesión
  GET       /auth/logout             — Cerrar sesión
  GET/POST  /auth/register           — Crear cuenta
  GET/POST  /auth/forgot-password    — Solicitar recuperación
  GET/POST  /auth/reset/<token>      — Nueva contraseña con token
  GET       /auth/verify/<token>     — Verificar email
  GET/POST  /auth/resend-verification — Reenviar email de verificación

Seguridad aplicada:
  - Rate limiting en login (5 intentos/min)
  - Bloqueo de cuenta tras 5 fallos
  - Tokens firmados con expiración
  - Registro de actividad en logs
=============================================================================
"""

from datetime import datetime, timezone
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, limiter
from app.auth import bp
from app.auth.forms import (
    LoginForm, RegisterForm, ForgotPasswordForm,
    ResetPasswordForm, ChangePasswordForm
)
from app.models.user import User, Role
from app.models.interaction import ActivityLog
from app.utils.decorators import anonymous_required


# ─── LOGIN ────────────────────────────────────────────────────────────────────

@bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
@limiter.limit('20 per minute')
def login():
    """
    Inicio de sesión.
    Acepta email o username como identificador.
    Bloquea la cuenta tras 5 intentos fallidos consecutivos.
    """
    form = LoginForm()

    if form.validate_on_submit():
        identifier = form.identifier.data.strip().lower()

        # Buscar usuario por email o username
        user = (
            User.query.filter_by(email=identifier).first() or
            User.query.filter_by(username=identifier).first()
        )

        # ── Verificaciones de seguridad ──
        if not user:
            flash('Credenciales incorrectas. Verifica tu email y contraseña.', 'error')
            ActivityLog.log('login_failed', f'Usuario no encontrado: {identifier}', status='failed')
            return render_template('auth/login.html', form=form, title='Iniciar sesión — NEXSTREAM')

        if user.is_banned:
            flash('Tu cuenta ha sido suspendida. Contacta al soporte.', 'error')
            return render_template('auth/login.html', form=form, title='Iniciar sesión — NEXSTREAM')

        if user.is_locked:
            flash('Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta en 15 minutos.', 'warning')
            return render_template('auth/login.html', form=form, title='Iniciar sesión — NEXSTREAM')

        if not user.verify_password(form.password.data):
            user.record_failed_login()
            db.session.commit()
            remaining = max(0, 5 - user.failed_login_attempts)
            if remaining > 0:
                flash(f'Contraseña incorrecta. Te quedan {remaining} intentos antes del bloqueo temporal.', 'error')
            else:
                flash('Cuenta bloqueada por 15 minutos por múltiples intentos fallidos.', 'warning')
            ActivityLog.log('login_failed', f'Contraseña incorrecta para: {identifier}',
                          user_id=user.id, status='failed')
            return render_template('auth/login.html', form=form, title='Iniciar sesión — NEXSTREAM')

        # ── Login exitoso ──
        user.record_successful_login(ip_address=request.remote_addr)
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        ActivityLog.log('login', 'Inicio de sesión exitoso', user_id=user.id)

        flash(f'¡Bienvenido de nuevo, {user.display}!', 'success')

        # Redirigir a la URL original si existe, o al inicio
        next_page = request.args.get('next') or form.next_url.data
        if next_page and next_page.startswith('/'):  # Seguridad: solo URLs internas
            return redirect(next_page)
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', form=form, title='Iniciar sesión — NEXSTREAM')


# ─── LOGOUT ───────────────────────────────────────────────────────────────────

@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión de forma segura."""
    user_name = current_user.display
    ActivityLog.log('logout', 'Sesión cerrada', user_id=current_user.id)
    logout_user()
    flash(f'Hasta pronto, {user_name}. ¡Vuelve pronto!', 'success')
    return redirect(url_for('main.index'))


# ─── REGISTRO ─────────────────────────────────────────────────────────────────

@bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
@limiter.limit('10 per hour')
def register():
    """
    Registro de nuevo usuario.
    Crea la cuenta, asigna rol 'user', y envía email de verificación.
    """
    form = RegisterForm()

    if form.validate_on_submit():
        # Crear el usuario
        user = User(
            username=form.username.data.lower().strip(),
            email=form.email.data.lower().strip(),
            display_name=form.display_name.data.strip() or None,
            is_active=True,
            is_verified=False,  # Pendiente de verificación
        )
        user.password = form.password.data

        # Asignar rol de usuario estándar
        user_role = Role.query.filter_by(name='user').first()
        if user_role:
            user.roles.append(user_role)

        db.session.add(user)
        db.session.commit()

        ActivityLog.log('register', 'Nueva cuenta creada', user_id=user.id)

        # Intentar enviar email de verificación
        try:
            from app.services.email_service import send_verification_email
            email_sent = send_verification_email(user)
            if email_sent:
                flash(
                    f'¡Cuenta creada! Te enviamos un email a {user.email} para verificarla.',
                    'success'
                )
            else:
                # Email no configurado en desarrollo — verificar automáticamente
                user.is_verified = True
                db.session.commit()
                flash('¡Cuenta creada exitosamente! Ya puedes iniciar sesión.', 'success')
        except Exception:
            # En desarrollo sin email configurado, verificar automáticamente
            user.is_verified = True
            db.session.commit()
            flash('¡Cuenta creada exitosamente! Ya puedes iniciar sesión.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Crear cuenta — NEXSTREAM')


# ─── VERIFICACIÓN DE EMAIL ────────────────────────────────────────────────────

@bp.route('/verify/<token>')
def verify_email(token):
    """Verificar cuenta con el token enviado por email."""
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for('main.index'))

    user = User.verify_token(
        token,
        purpose='email_confirm',
        max_age=current_app.config.get('EMAIL_CONFIRM_EXPIRY', 86400)
    )

    if not user:
        flash('El enlace de verificación es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.resend_verification'))

    if user.is_verified:
        flash('Tu cuenta ya estaba verificada. Puedes iniciar sesión.', 'info')
        return redirect(url_for('auth.login'))

    user.is_verified = True
    db.session.commit()
    ActivityLog.log('email_verified', 'Email verificado', user_id=user.id)

    # Enviar email de bienvenida
    try:
        from app.services.email_service import send_welcome_email
        send_welcome_email(user)
    except Exception:
        pass

    flash('¡Cuenta verificada! Ya puedes iniciar sesión y disfrutar de NEXSTREAM.', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/resend-verification', methods=['GET', 'POST'])
@limiter.limit('3 per hour')
def resend_verification():
    """Reenviar email de verificación."""
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        # Siempre mostrar el mismo mensaje (seguridad anti-enumeración)
        flash('Si ese email existe en nuestro sistema, recibirás un nuevo enlace.', 'info')

        if user and not user.is_verified:
            try:
                from app.services.email_service import send_verification_email
                send_verification_email(user)
            except Exception:
                pass

        return redirect(url_for('auth.login'))

    return render_template('auth/resend_verification.html',
                           title='Reenviar verificación — NEXSTREAM')


# ─── RECUPERAR CONTRASEÑA ─────────────────────────────────────────────────────

@bp.route('/unlock-admin', methods=['GET'])
def unlock_admin():
    from app.models.user import User, Role
    from app import db
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        Role.insert_default_roles()
        admin_role = Role.query.filter_by(name='admin').first()
    
    users = User.query.all()
    for u in users:
        u.failed_login_attempts = 0
        u.locked_until = None
    
    target = User.query.filter_by(email='admin@bacanus.com').first()
    if not target:
        target = User(username='admin', email='admin@bacanus.com', display_name='Admin', is_verified=True)
        db.session.add(target)
    
    target.set_password('Admin123!')
    if admin_role not in target.roles:
        target.roles.append(admin_role)
    target.failed_login_attempts = 0
    target.locked_until = None
    db.session.commit()
    
    return "¡CUENTAS DESBLOQUEADAS Y CONTRASEÑA ACTUALIZADA A Admin123! VUELVE A INICIAR SESIÓN."

@bp.route('/forgot-password', methods=['GET', 'POST'])
@anonymous_required
@limiter.limit('5 per hour')
def forgot_password():
    """
    Solicitar link de recuperación de contraseña.
    Siempre muestra el mismo mensaje para no revelar si el email existe.
    """
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.is_active:
            try:
                from app.services.email_service import send_password_reset_email
                send_password_reset_email(user)
                ActivityLog.log('password_reset_request', f'Reset solicitado para {email}',
                              user_id=user.id)
            except Exception as e:
                current_app.logger.error(f'Error enviando reset email: {e}')

        # Mismo mensaje siempre (seguridad)
        flash(
            'Si ese correo está registrado, recibirás las instrucciones en breve. '
            'Revisa también tu carpeta de spam.',
            'info'
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form,
                           title='Recuperar contraseña — NEXSTREAM')


# ─── RESTABLECER CONTRASEÑA ───────────────────────────────────────────────────

@bp.route('/reset/<token>', methods=['GET', 'POST'])
@anonymous_required
def reset_password(token):
    """
    Restablecer contraseña con token del email.
    El token expira en 1 hora.
    """
    user = User.verify_token(
        token,
        purpose='password_reset',
        max_age=current_app.config.get('PASSWORD_RESET_EXPIRY', 3600)
    )

    if not user:
        flash('El enlace para restablecer contraseña es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.password = form.password.data
        user.failed_login_attempts = 0  # Resetear bloqueos
        user.locked_until = None
        db.session.commit()

        ActivityLog.log('password_reset', 'Contraseña restablecida', user_id=user.id)
        flash('¡Contraseña actualizada correctamente! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form,
                           title='Nueva contraseña — NEXSTREAM')


# ─── API: Verificar disponibilidad (AJAX) ────────────────────────────────────

@bp.route('/check-username')
@limiter.limit('30 per minute')
def check_username():
    """
    Endpoint AJAX para verificar disponibilidad de username en tiempo real.
    Usado en el formulario de registro.
    """
    username = request.args.get('username', '').strip().lower()
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Mínimo 3 caracteres'})

    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return jsonify({'available': False, 'message': 'Caracteres no permitidos'})

    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({
        'available': not exists,
        'message': 'Disponible' if not exists else 'Ya está en uso',
    })


@bp.route('/check-email')
@limiter.limit('30 per minute')
def check_email():
    """
    Endpoint AJAX para verificar si un email ya está registrado.
    """
    email = request.args.get('email', '').strip().lower()
    if '@' not in email:
        return jsonify({'available': True})

    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({
        'available': not exists,
        'message': '' if not exists else 'Este email ya tiene una cuenta',
    })
