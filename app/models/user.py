"""
=============================================================================
NEXSTREAM — Modelos de Base de Datos: Usuarios y Autenticación
=============================================================================
Archivo: app/models/user.py
Descripción: Modelos SQLAlchemy para usuarios, roles y permisos.

Modelos:
    - Role: Roles de usuario (admin, moderator, user)
    - User: Usuarios registrados con Flask-Login
    - PasswordResetToken: Tokens para recuperación de contraseña
=============================================================================
"""

from datetime import datetime, timezone
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from extensions import db, bcrypt


# ─── Tabla de Asociación: Usuarios ↔ Roles ────────────────────────────────────
# Relación muchos a muchos entre usuarios y roles
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
)


class Role(db.Model):
    """
    ─── Modelo de Rol ────────────────────────────────────────────────────────
    Define los roles disponibles en la plataforma.

    Roles predefinidos:
        - admin: Acceso total a todas las funciones
        - moderator: Gestión de contenido y comentarios
        - user: Usuario estándar
    """

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Permisos como string separado por comas (ej: "manage_content,manage_users")
    permissions = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Role {self.name}>'

    def has_permission(self, permission: str) -> bool:
        """Verificar si el rol tiene un permiso específico."""
        if not self.permissions:
            return False
        return permission in self.permissions.split(',')

    @staticmethod
    def insert_default_roles():
        """Insertar roles predeterminados en la base de datos."""
        roles = {
            'admin': 'Administrador completo de la plataforma',
            'moderator': 'Gestión de contenido y moderación',
            'user': 'Usuario registrado estándar',
        }
        for name, description in roles.items():
            role = Role.query.filter_by(name=name).first()
            if role is None:
                role = Role(name=name, description=description)
                db.session.add(role)
        db.session.commit()


class User(UserMixin, db.Model):
    """
    ─── Modelo de Usuario ────────────────────────────────────────────────────
    Usuario registrado en la plataforma.
    Hereda de UserMixin para compatibilidad con Flask-Login.

    Características:
        - Hash de contraseña con bcrypt
        - Sistema de roles y permisos
        - Verificación de email
        - Tema personalizable (dark/light)
        - Progreso de visualización
    """

    __tablename__ = 'users'

    # ─── Identificación ───────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # ─── Perfil ───────────────────────────────────────────────────────────────
    display_name = db.Column(db.String(120))           # Nombre para mostrar
    bio = db.Column(db.Text)                            # Biografía opcional
    avatar = db.Column(db.String(255))                  # Ruta a la imagen de avatar
    banner = db.Column(db.String(255))                  # Banner de perfil

    # ─── Estado ───────────────────────────────────────────────────────────────
    is_active = db.Column(db.Boolean, default=True)     # Cuenta activa/suspendida
    is_verified = db.Column(db.Boolean, default=False)  # Email verificado
    is_banned = db.Column(db.Boolean, default=False)    # Usuario baneado

    # ─── Configuración ────────────────────────────────────────────────────────
    theme = db.Column(db.String(10), default='dark')    # Tema: 'dark' o 'light'
    language = db.Column(db.String(10), default='es')   # Idioma preferido
    autoplay = db.Column(db.Boolean, default=True)      # Autoplay de siguiente episodio
    email_notifications = db.Column(db.Boolean, default=True)

    # ─── Seguridad ────────────────────────────────────────────────────────────
    login_count = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))  # IPv6 puede tener hasta 45 chars
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)     # Cuenta bloqueada hasta...

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                            backref=db.backref('users', lazy=True))

    # Las relaciones con contenido se definen usando strings para evitar imports circulares
    favorites = db.relationship('Favorite', back_populates='user',
                                cascade='all, delete-orphan', lazy='dynamic')
    watch_history = db.relationship('WatchHistory', back_populates='user',
                                    cascade='all, delete-orphan', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='user',
                               cascade='all, delete-orphan', lazy='dynamic')
    ratings = db.relationship('Rating', back_populates='user',
                              cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    # ─── Contraseña ───────────────────────────────────────────────────────────

    @property
    def password(self):
        """La contraseña no es accesible directamente (solo su hash)."""
        raise AttributeError('La contraseña no es legible directamente.')

    @password.setter
    def password(self, plain_password: str):
        """Genera y almacena el hash de la contraseña con bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def verify_password(self, plain_password: str) -> bool:
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    # ─── Roles y Permisos ─────────────────────────────────────────────────────

    def has_role(self, role_name: str) -> bool:
        """Verifica si el usuario tiene un rol específico."""
        return any(role.name == role_name for role in self.roles)

    @property
    def is_admin(self) -> bool:
        """True si el usuario es administrador."""
        return self.has_role('admin')

    @property
    def is_moderator(self) -> bool:
        """True si el usuario es moderador o admin."""
        return self.has_role('admin') or self.has_role('moderator')

    def add_role(self, role_name: str) -> None:
        """Añadir un rol al usuario."""
        role = Role.query.filter_by(name=role_name).first()
        if role and not self.has_role(role_name):
            self.roles.append(role)

    def remove_role(self, role_name: str) -> None:
        """Eliminar un rol del usuario."""
        role = Role.query.filter_by(name=role_name).first()
        if role in self.roles:
            self.roles.remove(role)

    # ─── Bloqueo de Cuenta ────────────────────────────────────────────────────

    @property
    def is_locked(self) -> bool:
        """True si la cuenta está temporalmente bloqueada."""
        if self.locked_until:
            return datetime.now(timezone.utc) < self.locked_until.replace(tzinfo=timezone.utc)
        return False

    def record_failed_login(self) -> None:
        """Registrar un intento de login fallido. Bloquear tras 5 intentos."""
        from datetime import timedelta
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)

    def record_successful_login(self, ip_address: str = None) -> None:
        """Registrar un login exitoso y resetear intentos fallidos."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.login_count += 1
        self.last_login = datetime.now(timezone.utc)
        self.last_login_ip = ip_address

    # ─── Tokens de Seguridad ──────────────────────────────────────────────────

    def generate_token(self, purpose: str) -> str:
        """
        Genera un token firmado para verificación de email o reset de contraseña.

        Args:
            purpose: 'email_confirm' o 'password_reset'

        Returns:
            str: Token URL-safe firmado con expiración
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'purpose': purpose}, salt=purpose)

    @staticmethod
    def verify_token(token: str, purpose: str, max_age: int = None) -> 'User | None':
        """
        Verifica un token y devuelve el usuario asociado.

        Args:
            token: Token a verificar
            purpose: Propósito esperado ('email_confirm' o 'password_reset')
            max_age: Tiempo máximo en segundos (usa config si no se especifica)

        Returns:
            User: El usuario si el token es válido, None en caso contrario
        """
        if max_age is None:
            max_age = current_app.config.get('PASSWORD_RESET_EXPIRY', 3600)

        try:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            data = s.loads(token, salt=purpose, max_age=max_age)
            if data.get('purpose') != purpose:
                return None
            return User.query.get(data['user_id'])
        except (SignatureExpired, BadSignature, Exception):
            return None

    # ─── Propiedades de Perfil ────────────────────────────────────────────────

    @property
    def avatar_url(self) -> str:
        """URL del avatar del usuario o imagen por defecto."""
        if self.avatar:
            return f'/static/uploads/avatars/{self.avatar}'
        return '/static/images/default-avatar.webp'

    @property
    def display(self) -> str:
        """Nombre para mostrar: display_name o username."""
        return self.display_name or self.username

    def to_dict(self) -> dict:
        """Serializar usuario a diccionario (para API)."""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display,
            'avatar_url': self.avatar_url,
            'is_admin': self.is_admin,
            'is_moderator': self.is_moderator,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
