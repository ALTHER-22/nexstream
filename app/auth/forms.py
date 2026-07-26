"""
=============================================================================
NEXSTREAM — Formularios de Autenticación
=============================================================================
Archivo: app/auth/forms.py
Descripción: Formularios Flask-WTF con validaciones personalizadas para
             login, registro, recuperación y cambio de contraseña.

Validaciones implementadas:
  - Email único en BD
  - Username único en BD
  - Fortaleza de contraseña (min 8 chars, mayús, número)
  - Confirmación de contraseña
  - CSRF automático vía Flask-WTF
=============================================================================
"""

import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField,
    TextAreaField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo,
    ValidationError, Regexp, Optional
)


# ─── Validadores personalizados ───────────────────────────────────────────────

def validate_password_strength(form, field):
    """
    Valida que la contraseña tenga al menos:
    - 8 caracteres
    - Una letra mayúscula
    - Una letra minúscula
    - Un número
    """
    password = field.data
    if not password:
        return
    errors = []
    if len(password) < 8:
        errors.append('mínimo 8 caracteres')
    if not re.search(r'[A-Z]', password):
        errors.append('al menos una mayúscula')
    if not re.search(r'[a-z]', password):
        errors.append('al menos una minúscula')
    if not re.search(r'\d', password):
        errors.append('al menos un número')
    if errors:
        raise ValidationError(f'La contraseña requiere: {", ".join(errors)}.')


# ─── Formulario de Login ──────────────────────────────────────────────────────

class LoginForm(FlaskForm):
    """
    Formulario de inicio de sesión.
    Acepta email o username para mayor flexibilidad.
    """

    # Puede ser email o username
    identifier = StringField(
        'Email o usuario',
        validators=[
            DataRequired(message='Ingresa tu email o nombre de usuario.'),
            Length(min=3, max=255, message='Debe tener entre 3 y 255 caracteres.'),
        ],
        render_kw={
            'placeholder': 'correo@ejemplo.com o @usuario',
            'autocomplete': 'username email',
            'id': 'loginIdentifier',
        }
    )

    password = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='Ingresa tu contraseña.'),
            Length(min=6, max=128),
        ],
        render_kw={
            'placeholder': 'Tu contraseña',
            'autocomplete': 'current-password',
            'id': 'loginPassword',
        }
    )

    remember_me = BooleanField(
        'Mantener sesión iniciada',
        default=False,
        render_kw={'id': 'loginRemember'}
    )

    # Campo oculto para redirigir después del login
    next_url = HiddenField()


# ─── Formulario de Registro ───────────────────────────────────────────────────

class RegisterForm(FlaskForm):
    """
    Formulario de registro de nuevo usuario.
    Valida unicidad de email y username contra la BD.
    """

    username = StringField(
        'Nombre de usuario',
        validators=[
            DataRequired(message='Elige un nombre de usuario.'),
            Length(min=3, max=80, message='Debe tener entre 3 y 80 caracteres.'),
            Regexp(
                r'^[a-zA-Z0-9_.-]+$',
                message='Solo letras, números, puntos, guiones y guiones bajos.'
            ),
        ],
        render_kw={
            'placeholder': 'mi_usuario_123',
            'autocomplete': 'username',
            'id': 'registerUsername',
        }
    )

    email = StringField(
        'Correo electrónico',
        validators=[
            DataRequired(message='Ingresa tu correo electrónico.'),
            Email(message='Ingresa un email válido.'),
            Length(max=255),
        ],
        render_kw={
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'email',
            'id': 'registerEmail',
            'type': 'email',
        }
    )

    display_name = StringField(
        'Nombre para mostrar',
        validators=[
            Optional(),
            Length(max=120, message='Máximo 120 caracteres.'),
        ],
        render_kw={
            'placeholder': 'Como quieres que te llamen',
            'id': 'registerDisplayName',
        }
    )

    password = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='Elige una contraseña.'),
            validate_password_strength,
        ],
        render_kw={
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password',
            'id': 'registerPassword',
        }
    )

    password2 = PasswordField(
        'Confirmar contraseña',
        validators=[
            DataRequired(message='Confirma tu contraseña.'),
            EqualTo('password', message='Las contraseñas no coinciden.'),
        ],
        render_kw={
            'placeholder': 'Repite tu contraseña',
            'autocomplete': 'new-password',
            'id': 'registerPassword2',
        }
    )

    accept_terms = BooleanField(
        'Acepto los términos de uso y política de privacidad',
        validators=[
            DataRequired(message='Debes aceptar los términos para registrarte.')
        ],
        render_kw={'id': 'registerTerms'}
    )

    def validate_username(self, field):
        """Verificar que el username no esté en uso."""
        from app.models.user import User
        user = User.query.filter_by(username=field.data.lower()).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Elige otro.')

    def validate_email(self, field):
        """Verificar que el email no esté registrado."""
        from app.models.user import User
        user = User.query.filter_by(email=field.data.lower()).first()
        if user:
            raise ValidationError('Este correo ya tiene una cuenta. ¿Quieres iniciar sesión?')


# ─── Formulario de Recuperar Contraseña ──────────────────────────────────────

class ForgotPasswordForm(FlaskForm):
    """
    Solicitar link de recuperación de contraseña por email.
    """

    email = StringField(
        'Correo electrónico',
        validators=[
            DataRequired(message='Ingresa tu correo electrónico.'),
            Email(message='Ingresa un email válido.'),
        ],
        render_kw={
            'placeholder': 'El email con el que te registraste',
            'autocomplete': 'email',
            'id': 'forgotEmail',
            'type': 'email',
        }
    )


# ─── Formulario de Nueva Contraseña ──────────────────────────────────────────

class ResetPasswordForm(FlaskForm):
    """
    Formulario para establecer nueva contraseña tras recuperación.
    """

    password = PasswordField(
        'Nueva contraseña',
        validators=[
            DataRequired(message='Ingresa tu nueva contraseña.'),
            validate_password_strength,
        ],
        render_kw={
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password',
            'id': 'resetPassword',
        }
    )

    password2 = PasswordField(
        'Confirmar contraseña',
        validators=[
            DataRequired(message='Confirma tu nueva contraseña.'),
            EqualTo('password', message='Las contraseñas no coinciden.'),
        ],
        render_kw={
            'placeholder': 'Repite tu nueva contraseña',
            'autocomplete': 'new-password',
            'id': 'resetPassword2',
        }
    )


# ─── Formulario de Cambio de Contraseña ──────────────────────────────────────

class ChangePasswordForm(FlaskForm):
    """
    Para usuarios autenticados que quieren cambiar su contraseña
    desde el perfil (requiere contraseña actual).
    """

    current_password = PasswordField(
        'Contraseña actual',
        validators=[DataRequired(message='Ingresa tu contraseña actual.')],
        render_kw={
            'placeholder': 'Tu contraseña actual',
            'autocomplete': 'current-password',
            'id': 'currentPassword',
        }
    )

    new_password = PasswordField(
        'Nueva contraseña',
        validators=[
            DataRequired(message='Ingresa tu nueva contraseña.'),
            validate_password_strength,
        ],
        render_kw={
            'placeholder': 'Nueva contraseña',
            'autocomplete': 'new-password',
            'id': 'newPassword',
        }
    )

    new_password2 = PasswordField(
        'Confirmar nueva contraseña',
        validators=[
            DataRequired(message='Confirma tu nueva contraseña.'),
            EqualTo('new_password', message='Las contraseñas no coinciden.'),
        ],
        render_kw={
            'placeholder': 'Repite la nueva contraseña',
            'autocomplete': 'new-password',
            'id': 'newPassword2',
        }
    )
