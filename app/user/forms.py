"""
=============================================================================
NEXSTREAM — Formularios de Usuario
=============================================================================
Archivo: app/user/forms.py
Descripción: Formularios para la gestión del perfil de usuario y configuración.
=============================================================================
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from flask_login import current_user
from app.models.user import User


class ProfileForm(FlaskForm):
    """Formulario para actualizar el perfil público."""

    display_name = StringField(
        'Nombre para mostrar',
        validators=[Optional(), Length(max=120)],
        render_kw={'placeholder': '¿Cómo quieres que te llamen?'}
    )

    username = StringField(
        'Nombre de usuario',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={'placeholder': 'Tu nombre de usuario único'}
    )

    bio = TextAreaField(
        'Biografía',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Cuéntanos un poco sobre ti...', 'rows': 4}
    )

    avatar = FileField(
        'Cambiar Avatar',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'avif'], 'Solo imágenes (JPG, PNG, WEBP).')
        ]
    )

    def validate_username(self, field):
        """Verificar que el nuevo username no esté en uso por otro usuario."""
        if field.data.lower() != current_user.username.lower():
            user = User.query.filter_by(username=field.data.lower()).first()
            if user:
                raise ValidationError('Este nombre de usuario ya está en uso.')


class SettingsForm(FlaskForm):
    """Formulario de configuración de la cuenta."""

    theme = SelectField(
        'Tema de la plataforma',
        choices=[('dark', 'Modo Oscuro (Recomendado)'), ('light', 'Modo Claro')],
        default='dark'
    )

    language = SelectField(
        'Idioma preferido',
        choices=[('es', 'Español'), ('en', 'English')],
        default='es'
    )

    autoplay = BooleanField(
        'Reproducir siguiente episodio automáticamente',
        default=True
    )

    email_notifications = BooleanField(
        'Recibir correos sobre nuevos lanzamientos y recomendaciones',
        default=True
    )
