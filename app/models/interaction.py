"""
=============================================================================
NEXSTREAM — Modelos de Interacción
=============================================================================
Archivo: app/models/interaction.py
Descripción: Modelos para las interacciones de usuarios con el contenido.

Modelos:
    - Favorite: Sistema de favoritos
    - WatchHistory: Historial de visualización y progreso
    - Comment: Comentarios con respuestas (sistema threaded)
    - Rating: Valoraciones de 1 a 10
    - Notification: Notificaciones del sistema
    - ActivityLog: Log de actividad para auditoría
=============================================================================
"""

from datetime import datetime, timezone
from extensions import db


class Favorite(db.Model):
    """
    ─── Favoritos ────────────────────────────────────────────────────────────
    Un usuario puede marcar series y películas como favoritas.
    Relación muchos a muchos entre User y (Series | Movie).
    """

    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Un favorito puede ser serie O película (nunca ambos)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id', ondelete='CASCADE'),
                          nullable=True, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'),
                         nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='favorites')
    series = db.relationship('Series', back_populates='favorites')
    movie = db.relationship('Movie', back_populates='favorites')

    __table_args__ = (
        # Un usuario solo puede tener un favorito por serie
        db.UniqueConstraint('user_id', 'series_id', name='unique_user_series_favorite'),
        # Un usuario solo puede tener un favorito por película
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_favorite'),
    )

    def __repr__(self):
        content = self.series.title if self.series else (self.movie.title if self.movie else '?')
        return f'<Favorite {self.user.username} → {content}>'

    @property
    def content(self):
        """Retorna el contenido asociado (serie o película)."""
        return self.series or self.movie

    @property
    def content_type(self) -> str:
        """Tipo de contenido: 'series' o 'movie'."""
        return 'series' if self.series_id else 'movie'


class WatchHistory(db.Model):
    """
    ─── Historial de Visualización ───────────────────────────────────────────
    Registra qué contenido ha visto cada usuario y su progreso.

    Para episodios: guarda el segundo exacto donde quedó.
    Para películas: igual.

    Usado para:
        - Sección "Continuar viendo"
        - Marcar episodios como vistos
        - Calcular estadísticas de plataforma
    """

    __tablename__ = 'watch_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Contenido visto
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id', ondelete='CASCADE'),
                           nullable=True, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'),
                         nullable=True, index=True)

    # ─── Progreso ─────────────────────────────────────────────────────────────
    progress = db.Column(db.Integer, default=0)    # Segundo donde se quedó
    duration = db.Column(db.Integer, default=0)    # Duración total en segundos
    completed = db.Column(db.Boolean, default=False)  # Si terminó el contenido

    # ─── Timestamps ───────────────────────────────────────────────────────────
    watched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='watch_history')
    episode = db.relationship('Episode', back_populates='watch_history')
    movie = db.relationship('Movie')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'episode_id', name='unique_user_episode_history'),
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_history'),
    )

    def __repr__(self):
        return f'<WatchHistory user={self.user_id} progress={self.progress}s>'

    @property
    def progress_percentage(self) -> float:
        """Porcentaje de progreso (0-100)."""
        if self.duration and self.duration > 0:
            return min((self.progress / self.duration) * 100, 100)
        return 0.0

    def update_progress(self, current_second: int, total_duration: int) -> None:
        """Actualizar progreso de visualización."""
        self.progress = current_second
        self.duration = total_duration
        # Marcar como completado si llegó al 90%
        self.completed = (current_second / total_duration >= 0.9) if total_duration > 0 else False
        self.last_updated = datetime.now(timezone.utc)
        db.session.commit()


class Comment(db.Model):
    """
    ─── Comentarios ──────────────────────────────────────────────────────────
    Sistema de comentarios con respuestas anidadas (un nivel).
    Los comentarios pueden ser en series o películas.

    Moderación:
        - is_approved: Comentario visible
        - is_flagged: Marcado por usuarios
        - is_pinned: Fijado por moderador
    """

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Contenido al que pertenece
    series_id = db.Column(db.Integer, db.ForeignKey('series.id', ondelete='CASCADE'),
                          nullable=True, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'),
                         nullable=True, index=True)

    # Respuesta a otro comentario (un nivel de anidación)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'),
                          nullable=True, index=True)

    # ─── Contenido ────────────────────────────────────────────────────────────
    body = db.Column(db.Text, nullable=False)

    # ─── Moderación ───────────────────────────────────────────────────────────
    is_approved = db.Column(db.Boolean, default=True)    # Visible si True
    is_flagged = db.Column(db.Boolean, default=False)    # Reportado por usuarios
    is_pinned = db.Column(db.Boolean, default=False)     # Fijado por moderador
    flags_count = db.Column(db.Integer, default=0)       # Número de reportes

    # ─── Likes ────────────────────────────────────────────────────────────────
    likes_count = db.Column(db.Integer, default=0)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    is_edited = db.Column(db.Boolean, default=False)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='comments')
    series = db.relationship('Series', back_populates='comments')
    movie = db.relationship('Movie', back_populates='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                              cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Comment {self.id} by {self.user.username if self.user else "?"}>'

    @property
    def is_reply(self) -> bool:
        """True si es una respuesta a otro comentario."""
        return self.parent_id is not None


class Rating(db.Model):
    """
    ─── Valoraciones ─────────────────────────────────────────────────────────
    Valoraciones de 1 a 10 estrellas de usuarios sobre contenido.
    Un usuario solo puede valorar cada contenido una vez.
    """

    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id', ondelete='CASCADE'),
                          nullable=True, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'),
                         nullable=True, index=True)

    score = db.Column(db.Float, nullable=False)  # 1.0 a 10.0

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='ratings')
    series = db.relationship('Series', back_populates='ratings')
    movie = db.relationship('Movie', back_populates='ratings')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'series_id', name='unique_user_series_rating'),
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_rating'),
        db.CheckConstraint('score >= 1 AND score <= 10', name='check_rating_score'),
    )

    def __repr__(self):
        return f'<Rating {self.score}/10 by user={self.user_id}>'


class Notification(db.Model):
    """
    ─── Notificaciones ───────────────────────────────────────────────────────
    Sistema de notificaciones para usuarios.
    (Nuevo episodio, respuesta a comentario, etc.)
    """

    __tablename__ = 'notifications'

    TYPES = ['new_episode', 'comment_reply', 'system', 'achievement', 'promo']

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    type = db.Column(db.String(50), nullable=False)          # Tipo de notificación
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text)
    link = db.Column(db.String(500))                         # URL al hacer clic
    icon = db.Column(db.String(255))                         # Imagen/icono

    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ─── Relación ─────────────────────────────────────────────────────────────
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.type} for user={self.user_id}>'


class ActivityLog(db.Model):
    """
    ─── Log de Actividad ─────────────────────────────────────────────────────
    Registro de acciones importantes para auditoría.
    (Logins, cambios de contraseña, acciones admin, etc.)
    """

    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                        nullable=True, index=True)

    action = db.Column(db.String(100), nullable=False)  # 'login', 'register', etc.
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    extra_data = db.Column(db.Text)    # JSON adicional

    status = db.Column(db.String(20), default='success')  # success, failed, warning

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ─── Relación ─────────────────────────────────────────────────────────────
    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<ActivityLog {self.action} at {self.created_at}>'

    @staticmethod
    def log(action: str, description: str = None, user_id: int = None,
            ip_address: str = None, status: str = 'success') -> None:
        """
        Crear una entrada de log de forma estática.

        Uso:
            ActivityLog.log('login', 'Usuario inició sesión', user_id=1, ip_address='127.0.0.1')
        """
        from flask import request as flask_request
        log = ActivityLog(
            action=action,
            description=description,
            user_id=user_id,
            ip_address=ip_address or (flask_request.remote_addr if flask_request else None),
            user_agent=flask_request.user_agent.string if flask_request else None,
            status=status
        )
        db.session.add(log)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
