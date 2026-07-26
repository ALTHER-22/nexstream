"""
=============================================================================
NEXSTREAM — Rutas del Panel de Usuario
=============================================================================
Archivo: app/user/routes.py
Descripción: Gestión del perfil, historial, favoritos y configuración.
=============================================================================
"""

import os
import secrets
from flask import (
    render_template, redirect, url_for, flash,
    request, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from extensions import db
from app.user import bp
from app.user.forms import ProfileForm, SettingsForm
from app.auth.forms import ChangePasswordForm
from app.models.interaction import WatchHistory, Favorite, ActivityLog


def save_avatar(form_picture) -> str:
    """Procesa, redimensiona y guarda el avatar subido por el usuario."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'], 'avatars', picture_fn
    )

    # Crear directorio si no existe
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    # Redimensionar y guardar con Pillow
    output_size = (250, 250)
    i = Image.open(form_picture)
    
    # Recortar al centro si no es cuadrada
    width, height = i.size
    if width != height:
        new_size = min(width, height)
        left = (width - new_size) / 2
        top = (height - new_size) / 2
        right = (width + new_size) / 2
        bottom = (height + new_size) / 2
        i = i.crop((left, top, right, bottom))
        
    i.thumbnail(output_size)
    
    # Convertir a RGB si es necesario (ej: PNG transparente a JPG)
    if i.mode in ('RGBA', 'P') and f_ext.lower() in ('.jpg', '.jpeg'):
        i = i.convert('RGB')
        
    i.save(picture_path)

    # Borrar avatar anterior si no era el default
    if current_user.avatar:
        old_avatar_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 'avatars', current_user.avatar
        )
        if os.path.exists(old_avatar_path):
            try:
                os.remove(old_avatar_path)
            except Exception as e:
                current_app.logger.warning(f"No se pudo eliminar avatar anterior: {e}")

    return picture_fn


@bp.route('/')
@bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def profile():
    """Panel principal y edición de perfil."""
    form = ProfileForm()

    if form.validate_on_submit():
        if form.avatar.data:
            avatar_file = save_avatar(form.avatar.data)
            current_user.avatar = avatar_file

        current_user.display_name = form.display_name.data.strip() or None
        current_user.username = form.username.data.strip().lower()
        current_user.bio = form.bio.data.strip() or None
        db.session.commit()
        
        ActivityLog.log('profile_update', 'Perfil actualizado', user_id=current_user.id)
        flash('Tu perfil ha sido actualizado correctamente.', 'success')
        return redirect(url_for('user.profile'))

    elif request.method == 'GET':
        form.display_name.data = current_user.display_name
        form.username.data = current_user.username
        form.bio.data = current_user.bio

    return render_template('user/profile.html', form=form, title='Mi Perfil — NEXSTREAM')


@bp.route('/historial')
@login_required
def history():
    """Historial de visualización del usuario."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    history_paginated = WatchHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(WatchHistory.watched_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('user/history.html', 
                           pagination=history_paginated, 
                           title='Mi Historial — NEXSTREAM')


@bp.route('/historial/limpiar', methods=['POST'])
@login_required
def clear_history():
    """Borrar todo el historial de visualización del usuario."""
    WatchHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    ActivityLog.log('history_cleared', 'Historial borrado', user_id=current_user.id)
    flash('Tu historial de visualización ha sido borrado.', 'info')
    return redirect(url_for('user.history'))


@bp.route('/favoritos')
@login_required
def favorites():
    """Lista de seguimiento (Mi Lista)."""
    page = request.args.get('page', 1, type=int)
    per_page = 24
    
    favorites_paginated = Favorite.query.filter_by(
        user_id=current_user.id
    ).order_by(Favorite.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('user/favorites.html', 
                           pagination=favorites_paginated, 
                           title='Mi Lista — NEXSTREAM')


@bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def settings():
    """Configuración de cuenta (tema, notificaciones, cambio de password)."""
    settings_form = SettingsForm()
    password_form = ChangePasswordForm()

    # Manejar cambio de preferencias
    if 'submit_settings' in request.form and settings_form.validate_on_submit():
        current_user.theme = settings_form.theme.data
        current_user.language = settings_form.language.data
        current_user.autoplay = settings_form.autoplay.data
        current_user.email_notifications = settings_form.email_notifications.data
        db.session.commit()
        
        ActivityLog.log('settings_update', 'Preferencias actualizadas', user_id=current_user.id)
        flash('Preferencias guardadas correctamente.', 'success')
        return redirect(url_for('user.settings'))

    # Manejar cambio de contraseña
    if 'submit_password' in request.form and password_form.validate_on_submit():
        if current_user.verify_password(password_form.current_password.data):
            current_user.password = password_form.new_password.data
            db.session.commit()
            
            ActivityLog.log('password_change', 'Contraseña cambiada desde perfil', user_id=current_user.id)
            flash('Tu contraseña ha sido actualizada.', 'success')
            return redirect(url_for('user.settings'))
        else:
            flash('La contraseña actual es incorrecta.', 'error')

    # Cargar valores iniciales para settings (GET)
    if request.method == 'GET':
        settings_form.theme.data = current_user.theme
        settings_form.language.data = current_user.language
        settings_form.autoplay.data = current_user.autoplay
        settings_form.email_notifications.data = current_user.email_notifications

    return render_template('user/settings.html', 
                           settings_form=settings_form, 
                           password_form=password_form,
                           title='Configuración — NEXSTREAM')
