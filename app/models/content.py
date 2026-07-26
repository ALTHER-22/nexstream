"""
=============================================================================
NEXSTREAM — Modelos de Contenido
=============================================================================
Archivo: app/models/content.py
Descripción: Modelos SQLAlchemy para Series, Películas, Temporadas,
             Episodios, Categorías y Banners.

Jerarquía de contenido:
    Category (muchos a muchos con Series/Movie)
    Series → Season → Episode
    Movie (independiente)
    Banner (promocional)
=============================================================================
"""

from datetime import datetime, timezone
from extensions import db
from slugify import slugify


# ─── Tabla de Asociación: Series ↔ Categorías ────────────────────────────────
series_categories = db.Table(
    'series_categories',
    db.Column('series_id', db.Integer, db.ForeignKey('series.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
)

# ─── Tabla de Asociación: Películas ↔ Categorías ─────────────────────────────
movie_categories = db.Table(
    'movie_categories',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
)


class Category(db.Model):
    """
    ─── Categoría / Género ───────────────────────────────────────────────────
    Géneros y categorías de contenido (Acción, Drama, Terror, etc.)
    """

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))          # Nombre de ícono (Font Awesome, etc.)
    color = db.Column(db.String(7))          # Color hex de la categoría
    image = db.Column(db.String(255))        # Imagen de portada de la categoría
    order = db.Column(db.Integer, default=0) # Orden en la navegación
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Category {self.name}>'

    def save(self):
        """Guardar con auto-generación de slug."""
        if not self.slug:
            self.slug = slugify(self.name)
        db.session.add(self)
        db.session.commit()


class Series(db.Model):
    """
    ─── Serie de TV ──────────────────────────────────────────────────────────
    Serie con múltiples temporadas y episodios.

    Campos principales:
        - Información básica (título, sinopsis, año)
        - Metadata (director, actores, idioma, país)
        - Imágenes (portada, banner)
        - Estado (activa, finalizada, en pausa)
        - Estadísticas (vistas, valoración promedio)
    """

    __tablename__ = 'series'

    # ─── Identificación ───────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(280), unique=True, nullable=False, index=True)
    original_title = db.Column(db.String(255))  # Título original si es diferente

    # ─── Información ──────────────────────────────────────────────────────────
    synopsis = db.Column(db.Text)
    short_description = db.Column(db.String(500))  # Para tarjetas y previews
    year = db.Column(db.Integer)
    end_year = db.Column(db.Integer)     # Año de finalización (si terminó)
    director = db.Column(db.String(255))
    cast = db.Column(db.Text)            # Actores separados por coma
    country = db.Column(db.String(100))
    language = db.Column(db.String(50))
    duration_avg = db.Column(db.Integer) # Duración promedio de episodio en minutos

    # ─── Clasificación ────────────────────────────────────────────────────────
    age_rating = db.Column(db.String(10), default='PG')  # G, PG, PG-13, R, NC-17
    content_advisory = db.Column(db.String(255))          # Advertencias de contenido

    # ─── Imágenes ─────────────────────────────────────────────────────────────
    cover = db.Column(db.String(255))    # Portada vertical (poster)
    banner = db.Column(db.String(255))   # Banner horizontal (hero image)
    thumbnail = db.Column(db.String(255)) # Miniatura pequeña

    # ─── Estado ───────────────────────────────────────────────────────────────
    STATUS_CHOICES = ['ongoing', 'completed', 'cancelled', 'upcoming', 'paused']
    status = db.Column(db.String(20), default='ongoing')
    is_active = db.Column(db.Boolean, default=True)     # Visible al público
    is_featured = db.Column(db.Boolean, default=False)  # Destacada en homepage
    is_trending = db.Column(db.Boolean, default=False)  # En tendencias

    # ─── Estadísticas ─────────────────────────────────────────────────────────
    views_count = db.Column(db.Integer, default=0)
    rating_avg = db.Column(db.Float, default=0.0)    # 0.0 a 10.0
    rating_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)

    # ─── SEO ──────────────────────────────────────────────────────────────────
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.String(500))
    meta_keywords = db.Column(db.String(500))

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    categories = db.relationship('Category', secondary=series_categories,
                                 lazy='subquery', backref=db.backref('series', lazy=True))
    seasons = db.relationship('Season', back_populates='series',
                              cascade='all, delete-orphan',
                              order_by='Season.number', lazy='dynamic')
    favorites = db.relationship('Favorite', back_populates='series',
                                cascade='all, delete-orphan', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='series',
                               cascade='all, delete-orphan', lazy='dynamic')
    ratings = db.relationship('Rating', back_populates='series',
                              cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Series {self.title}>'

    def save(self):
        """Guardar con auto-generación de slug."""
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f'{base_slug}-{self.year}' if self.year else base_slug
        db.session.add(self)
        db.session.commit()

    @property
    def cover_url(self) -> str:
        """URL de la portada o imagen por defecto."""
        if self.cover:
            if self.cover.startswith('/static/'):
                return self.cover
            return f'/static/uploads/covers/{self.cover}'
        return '/static/images/default-cover.svg'

    @property
    def banner_url(self) -> str:
        """URL del banner o imagen por defecto."""
        if self.banner:
            if self.banner.startswith('/static/'):
                return self.banner
            return f'/static/uploads/banners/{self.banner}'
        return '/static/images/default-banner.svg'

    @property
    def total_episodes(self) -> int:
        """Total de episodios en todas las temporadas."""
        return sum(season.episodes.count() for season in self.seasons)

    @property
    def total_seasons(self) -> int:
        """Número total de temporadas."""
        return self.seasons.count()

    @property
    def cast_list(self) -> list:
        """Lista de actores desde el campo de texto."""
        if self.cast:
            return [actor.strip() for actor in self.cast.split(',')]
        return []

    def increment_views(self) -> None:
        """Incrementar contador de visitas."""
        self.views_count += 1
        db.session.commit()

    def update_rating(self) -> None:
        """Recalcular rating promedio desde todas las valoraciones."""
        ratings = self.ratings.all()
        if ratings:
            self.rating_avg = sum(r.score for r in ratings) / len(ratings)
            self.rating_count = len(ratings)
        else:
            self.rating_avg = 0.0
            self.rating_count = 0
        db.session.commit()

    def to_dict(self) -> dict:
        """Serializar a diccionario para la API."""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'synopsis': self.synopsis,
            'year': self.year,
            'cover_url': self.cover_url,
            'banner_url': self.banner_url,
            'rating_avg': self.rating_avg,
            'views_count': self.views_count,
            'total_seasons': self.total_seasons,
            'total_episodes': self.total_episodes,
            'status': self.status,
            'categories': [c.name for c in self.categories],
        }


class Movie(db.Model):
    """
    ─── Película ─────────────────────────────────────────────────────────────
    Película independiente (no tiene temporadas ni episodios).
    Estructura similar a Series pero más simple.
    """

    __tablename__ = 'movies'

    # ─── Identificación ───────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(280), unique=True, nullable=False, index=True)
    original_title = db.Column(db.String(255))

    # ─── Información ──────────────────────────────────────────────────────────
    synopsis = db.Column(db.Text)
    short_description = db.Column(db.String(500))
    year = db.Column(db.Integer)
    director = db.Column(db.String(255))
    cast = db.Column(db.Text)
    country = db.Column(db.String(100))
    language = db.Column(db.String(50))
    duration = db.Column(db.Integer)     # Duración en minutos

    # ─── Clasificación ────────────────────────────────────────────────────────
    age_rating = db.Column(db.String(10), default='PG')
    content_advisory = db.Column(db.String(255))

    # ─── Archivo de Video ─────────────────────────────────────────────────────
    video_url = db.Column(db.String(500))        # URL del video (externo o local)
    video_file = db.Column(db.String(255))       # Nombre del archivo local
    subtitle_file = db.Column(db.String(255))    # Subtítulos VTT
    subtitle_lang = db.Column(db.String(50))     # Idioma de los subtítulos

    # ─── Imágenes ─────────────────────────────────────────────────────────────
    cover = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    thumbnail = db.Column(db.String(255))

    # ─── Estado ───────────────────────────────────────────────────────────────
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_trending = db.Column(db.Boolean, default=False)

    # ─── Estadísticas ─────────────────────────────────────────────────────────
    views_count = db.Column(db.Integer, default=0)
    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)

    # ─── SEO ──────────────────────────────────────────────────────────────────
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.String(500))
    meta_keywords = db.Column(db.String(500))

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    categories = db.relationship('Category', secondary=movie_categories,
                                 lazy='subquery', backref=db.backref('movies', lazy=True))
    favorites = db.relationship('Favorite', back_populates='movie',
                                cascade='all, delete-orphan', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='movie',
                               cascade='all, delete-orphan', lazy='dynamic')
    ratings = db.relationship('Rating', back_populates='movie',
                              cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Movie {self.title}>'

    def save(self):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f'{base_slug}-{self.year}' if self.year else base_slug
        db.session.add(self)
        db.session.commit()

    @property
    def cover_url(self) -> str:
        if self.cover:
            if self.cover.startswith('/static/'):
                return self.cover
            return f'/static/uploads/covers/{self.cover}'
        return '/static/images/default-cover.svg'

    @property
    def banner_url(self) -> str:
        if self.banner:
            if self.banner.startswith('/static/'):
                return self.banner
            return f'/static/uploads/banners/{self.banner}'
        return '/static/images/default-banner.svg'

    def increment_views(self) -> None:
        self.views_count += 1
        db.session.commit()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'synopsis': self.synopsis,
            'year': self.year,
            'duration': self.duration,
            'cover_url': self.cover_url,
            'rating_avg': self.rating_avg,
            'views_count': self.views_count,
            'categories': [c.name for c in self.categories],
        }


class Season(db.Model):
    """
    ─── Temporada ────────────────────────────────────────────────────────────
    Agrupa episodios de una serie bajo un número de temporada.
    """

    __tablename__ = 'seasons'

    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)   # Número de temporada (1, 2, 3...)
    title = db.Column(db.String(255))                # "Temporada 1" o título personalizado
    description = db.Column(db.Text)
    year = db.Column(db.Integer)
    cover = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    series = db.relationship('Series', back_populates='seasons')
    episodes = db.relationship('Episode', back_populates='season',
                               cascade='all, delete-orphan',
                               order_by='Episode.number', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('series_id', 'number', name='unique_series_season'),
    )

    def __repr__(self):
        return f'<Season {self.series.title if self.series else "?"} S{self.number}>'

    @property
    def display_title(self) -> str:
        """Título para mostrar."""
        return self.title or f'Temporada {self.number}'


class Episode(db.Model):
    """
    ─── Episodio ─────────────────────────────────────────────────────────────
    Episodio individual de una temporada.

    Soporta:
        - Video local o URL externa
        - Múltiples subtítulos
        - Miniaturas
        - Progreso de visualización (guardado en WatchHistory)
    """

    __tablename__ = 'episodes'

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)    # Número de episodio
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)                  # Duración en segundos

    # ─── Video ────────────────────────────────────────────────────────────────
    video_url = db.Column(db.String(500))             # URL externa (YouTube, drive, etc.)
    video_file = db.Column(db.String(255))            # Archivo local en /uploads/videos/
    embed_url = db.Column(db.String(500))             # URL para embed (iframe)

    # ─── Subtítulos ───────────────────────────────────────────────────────────
    subtitle_file = db.Column(db.String(255))         # Archivo VTT principal
    subtitle_lang = db.Column(db.String(50), default='es')

    # ─── Imagen ───────────────────────────────────────────────────────────────
    thumbnail = db.Column(db.String(255))

    # ─── Estado ───────────────────────────────────────────────────────────────
    is_active = db.Column(db.Boolean, default=True)
    is_free = db.Column(db.Boolean, default=True)     # Libre o premium

    # ─── Estadísticas ─────────────────────────────────────────────────────────
    views_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    season = db.relationship('Season', back_populates='episodes')
    watch_history = db.relationship('WatchHistory', back_populates='episode',
                                    cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('season_id', 'number', name='unique_season_episode'),
    )

    def __repr__(self):
        return f'<Episode S{self.season.number if self.season else "?"}E{self.number}: {self.title}>'

    @property
    def thumbnail_url(self) -> str:
        if self.thumbnail:
            if self.thumbnail.startswith('/static/'):
                return self.thumbnail
            return f'/static/uploads/thumbnails/{self.thumbnail}'
        return '/static/images/default-thumbnail.svg'

    @property
    def duration_formatted(self) -> str:
        """Duración en formato MM:SS o HH:MM:SS."""
        if not self.duration:
            return '--:--'
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours:
            return f'{hours}:{minutes:02d}:{seconds:02d}'
        return f'{minutes}:{seconds:02d}'

    def increment_views(self) -> None:
        self.views_count += 1
        db.session.commit()


class Banner(db.Model):
    """
    ─── Banner Publicitario / Promocional ────────────────────────────────────
    Banners para el hero section y secciones especiales.
    Pueden enlazar a contenido específico o URLs externas.
    """

    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(500))
    description = db.Column(db.Text)

    # ─── Imágenes ─────────────────────────────────────────────────────────────
    image_desktop = db.Column(db.String(255))   # Imagen para desktop
    image_mobile = db.Column(db.String(255))    # Imagen para móvil
    video_bg = db.Column(db.String(255))        # Video de fondo (opcional)

    # ─── Enlace ───────────────────────────────────────────────────────────────
    link_url = db.Column(db.String(500))        # URL del enlace
    link_text = db.Column(db.String(100), default='Ver ahora')

    # ─── Contenido asociado (opcional) ────────────────────────────────────────
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=True)

    # ─── Configuración ────────────────────────────────────────────────────────
    position = db.Column(db.Integer, default=0)  # Orden en el slider
    is_active = db.Column(db.Boolean, default=True)

    # ─── Período de vigencia ──────────────────────────────────────────────────
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Banner {self.title}>'

    @property
    def is_current(self) -> bool:
        """True si el banner está vigente en este momento."""
        now = datetime.now(timezone.utc)
        if self.starts_at and now < self.starts_at.replace(tzinfo=timezone.utc):
            return False
        if self.ends_at and now > self.ends_at.replace(tzinfo=timezone.utc):
            return False
        return self.is_active


class SiteConfig(db.Model):
    """
    ─── Configuración del Sitio ──────────────────────────────────────────────
    Almacena configuraciones dinámicas administrables desde el panel.
    Patrón clave-valor para máxima flexibilidad.
    """

    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    type = db.Column(db.String(20), default='text')  # text, boolean, integer, json
    label = db.Column(db.String(255))                # Label para el panel admin
    description = db.Column(db.Text)
    group = db.Column(db.String(100), default='general')  # Agrupar en el panel

    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<SiteConfig {self.key}={self.value}>'

    @staticmethod
    def get(key: str, default=None):
        """Obtener valor de configuración por clave."""
        config = SiteConfig.query.filter_by(key=key).first()
        return config.value if config else default

    @staticmethod
    def set(key: str, value: str) -> None:
        """Establecer valor de configuración."""
        config = SiteConfig.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
        else:
            config = SiteConfig(key=key, value=str(value))
            db.session.add(config)
        db.session.commit()
