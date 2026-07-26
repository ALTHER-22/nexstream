"""
=============================================================================
NEXSTREAM — Paquete de Modelos
=============================================================================
Archivo: app/models/__init__.py
Descripción: Exporta todos los modelos para facilitar las importaciones.

Uso:
    from app.models import User, Series, Episode, Category
    # En lugar de:
    from app.models.user import User
    from app.models.content import Series
=============================================================================
"""

# ─── Modelos de Usuario ───────────────────────────────────────────────────────
from app.models.user import User, Role

# ─── Modelos de Contenido ─────────────────────────────────────────────────────
from app.models.content import (
    Category,
    Series,
    Movie,
    Season,
    Episode,
    Banner,
    SiteConfig,
)

# ─── Modelos de Interacción ───────────────────────────────────────────────────
from app.models.interaction import (
    Favorite,
    WatchHistory,
    Comment,
    Rating,
    Notification,
    ActivityLog,
)

# ─── Modelos de Suscripción ───────────────────────────────────────────────────
from app.models.subscription import Plan, Subscription

# Lista de todos los modelos (útil para migraciones y shell context)
__all__ = [
    'User', 'Role',
    'Category', 'Series', 'Movie', 'Season', 'Episode', 'Banner', 'SiteConfig',
    'Favorite', 'WatchHistory', 'Comment', 'Rating', 'Notification', 'ActivityLog',
    'Plan', 'Subscription',
]
