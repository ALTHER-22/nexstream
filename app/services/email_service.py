"""
=============================================================================
NEXSTREAM — Servicio de Email
=============================================================================
Archivo: app/services/email_service.py
Descripción: Servicio centralizado para envío de emails transaccionales.
             Usa Flask-Mail con templates HTML.
=============================================================================
"""

from flask import current_app, url_for, render_template_string
from flask_mail import Message
from extensions import mail


# ─── Templates de Email (inline para el módulo base) ─────────────────────────

_EMAIL_BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width">
  <title>{subject}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0f; color: #ffffff; margin: 0; padding: 0; }}
    .wrap {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
    .logo {{ font-size: 28px; font-weight: 900; color: #e50914; letter-spacing: -0.04em;
             text-decoration: none; display: block; margin-bottom: 32px; }}
    .card {{ background: #16161e; border: 1px solid rgba(255,255,255,0.08);
             border-radius: 16px; padding: 32px; }}
    h1 {{ font-size: 24px; font-weight: 800; margin: 0 0 16px; color: #fff; }}
    p  {{ color: #b3b3cc; line-height: 1.6; margin: 0 0 16px; font-size: 15px; }}
    .btn {{ display: inline-block; background: #e50914; color: #ffffff !important;
            text-decoration: none; padding: 14px 32px; border-radius: 8px;
            font-weight: 700; font-size: 15px; margin: 8px 0 24px; }}
    .note {{ font-size: 13px; color: #6b6b8a; border-top: 1px solid rgba(255,255,255,0.06);
             padding-top: 16px; margin-top: 16px; }}
    .footer {{ text-align: center; padding-top: 32px; font-size: 12px; color: #3d3d52; }}
  </style>
</head>
<body>
  <div class="wrap">
    <a class="logo" href="{base_url}">NEXSTREAM</a>
    <div class="card">
      {content}
    </div>
    <div class="footer">
      &copy; 2026 NEXSTREAM &mdash; Tu universo de entretenimiento<br>
      Si no solicitaste este email, ignóralo con seguridad.
    </div>
  </div>
</body>
</html>
"""


def _send_email(to: str, subject: str, html_content: str) -> bool:
    """
    Función interna para enviar un email.
    Retorna True si se envió, False en caso de error.
    """
    try:
        base_url = current_app.config.get('SERVER_NAME') or 'http://localhost:5000'
        html_body = _EMAIL_BASE.format(
            subject=subject,
            base_url=base_url,
            content=html_content,
        )
        msg = Message(
            subject=f'NEXSTREAM — {subject}',
            recipients=[to],
            html=html_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'NEXSTREAM <noreply@nexstream.com>'),
        )
        mail.send(msg)
        current_app.logger.info(f'Email enviado a {to}: {subject}')
        return True
    except Exception as e:
        current_app.logger.error(f'Error enviando email a {to}: {e}')
        return False


def send_verification_email(user) -> bool:
    """
    Enviar email de verificación de cuenta.
    El usuario debe hacer clic en el link para activar su cuenta.
    """
    token = user.generate_token('email_confirm')

    with current_app.app_context():
        verify_url = url_for('auth.verify_email', token=token, _external=True)

    content = f"""
    <h1>Verifica tu cuenta</h1>
    <p>Hola <strong>{user.display}</strong>,</p>
    <p>Gracias por registrarte en NEXSTREAM. Para activar tu cuenta y
       comenzar a disfrutar del contenido, haz clic en el botón de abajo:</p>
    <a class="btn" href="{verify_url}">Verificar mi cuenta</a>
    <p class="note">Este enlace expira en 24 horas.<br>
    Si no creaste esta cuenta, ignora este email.</p>
    """
    return _send_email(user.email, 'Verifica tu cuenta', content)


def send_password_reset_email(user) -> bool:
    """
    Enviar email con link para restablecer contraseña.
    El token expira en 1 hora.
    """
    token = user.generate_token('password_reset')

    with current_app.app_context():
        reset_url = url_for('auth.reset_password', token=token, _external=True)

    content = f"""
    <h1>Restablecer contraseña</h1>
    <p>Hola <strong>{user.display}</strong>,</p>
    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta
       en NEXSTREAM. Haz clic en el botón para continuar:</p>
    <a class="btn" href="{reset_url}">Restablecer contraseña</a>
    <p class="note">Este enlace expira en 1 hora por seguridad.<br>
    Si no solicitaste esto, tu contraseña no ha cambiado y puedes ignorar este email.</p>
    """
    return _send_email(user.email, 'Restablecer contraseña', content)


def send_welcome_email(user) -> bool:
    """Bienvenida después de verificar la cuenta."""
    content = f"""
    <h1>Bienvenido a NEXSTREAM</h1>
    <p>Hola <strong>{user.display}</strong>,</p>
    <p>Tu cuenta ha sido verificada exitosamente. Ya puedes disfrutar
       de todo el contenido disponible en NEXSTREAM:</p>
    <a class="btn" href="http://localhost:5000">Explorar contenido</a>
    <p>Descubre series, películas, y mucho más. Tu universo de
       entretenimiento te espera.</p>
    """
    return _send_email(user.email, 'Bienvenido a NEXSTREAM', content)
