"""
=============================================================================
NEXSTREAM — API REST v1: Rutas Principales
=============================================================================
Archivo: app/api/routes.py
Descripción: Endpoints de la API REST para el frontend y clientes externos.

Endpoints:
  GET  /api/v1/status              — Health check
  GET  /api/v1/search?q=           — Búsqueda global con ranking
  GET  /api/v1/content/featured    — Contenido destacado para el hero
  GET  /api/v1/content/trending    — Tendencias
  GET  /api/v1/content/recent      — Últimas adiciones
  GET  /api/v1/series/<id>         — Detalle de serie
  GET  /api/v1/movies/<id>         — Detalle de película
  POST /api/v1/favorites/toggle    — Añadir/quitar favorito [auth]
  GET  /api/v1/favorites           — Lista de favoritos del usuario [auth]
  POST /api/v1/history/update      — Actualizar progreso [auth]
  GET  /api/v1/history             — Historial del usuario [auth]
  POST /api/v1/ratings             — Valorar contenido [auth]
  GET  /api/v1/categories          — Listar categorías
=============================================================================
"""

from datetime import datetime, timezone
from flask import jsonify, request, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_, func, desc
from extensions import db, limiter, cache
from app.api import bp
from app.models.content import Series, Movie, Category, Episode
from app.models.interaction import (
    Favorite, WatchHistory, Rating, ActivityLog
)
from app.utils.decorators import api_login_required


# ─── Helper: serialización segura ────────────────────────────────────────────

def _paginate_response(query, page, per_page, serializer):
    """Paginación reutilizable para cualquier query."""
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items':       [serializer(item) for item in paginated.items],
        'total':       paginated.total,
        'page':        paginated.page,
        'per_page':    paginated.per_page,
        'pages':       paginated.pages,
        'has_next':    paginated.has_next,
        'has_prev':    paginated.has_prev,
    }


def _series_brief(s):
    return {
        'id': s.id, 'title': s.title, 'slug': s.slug,
        'cover_url': s.cover_url, 'banner_url': s.banner_url,
        'year': s.year, 'rating_avg': float(s.rating_avg) if s.rating_avg else None,
        'rating_count': s.rating_count, 'status': s.status,
        'type': 'series',
        'categories': [{'id': c.id, 'name': c.name, 'slug': c.slug}
                       for c in s.categories[:3]],
        'is_favorite': _is_favorite('series', s.id),
    }


def _movie_brief(m):
    return {
        'id': m.id, 'title': m.title, 'slug': m.slug,
        'cover_url': m.cover_url, 'banner_url': m.banner_url,
        'year': m.year, 'duration': m.duration,
        'rating_avg': float(m.rating_avg) if m.rating_avg else None,
        'rating_count': m.rating_count,
        'type': 'movie',
        'categories': [{'id': c.id, 'name': c.name, 'slug': c.slug}
                       for c in m.categories[:3]],
        'is_favorite': _is_favorite('movie', m.id),
    }


def _is_favorite(content_type, content_id):
    """Check si el usuario actual tiene este contenido como favorito."""
    if not current_user.is_authenticated:
        return False
    q = Favorite.query.filter_by(user_id=current_user.id)
    if content_type == 'series':
        q = q.filter_by(series_id=content_id)
    else:
        q = q.filter_by(movie_id=content_id)
    return q.first() is not None


# ─── 1. HEALTH CHECK ─────────────────────────────────────────────────────────

@bp.route('/status')
def status():
    """Health check de la API."""
    return jsonify({
        'status':    'ok',
        'platform':  'NEXSTREAM',
        'version':   '2.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user':      current_user.display if current_user.is_authenticated else None,
    })


# ─── 2. BÚSQUEDA GLOBAL ───────────────────────────────────────────────────────

@bp.route('/search')
@limiter.limit('60 per minute')
def search():
    """
    Búsqueda global en series y películas.
    Busca en título, sinopsis y categorías.
    Parámetros: ?q=query&limit=10&type=all|series|movie
    """
    query_str = request.args.get('q', '').strip()
    limit      = min(int(request.args.get('limit', 10)), 50)
    filter_type = request.args.get('type', 'all')

    if len(query_str) < 2:
        return jsonify({'series': [], 'movies': [], 'query': query_str, 'total': 0})

    # Patrón de búsqueda LIKE
    pattern = f'%{query_str}%'

    series_results = []
    movie_results  = []

    if filter_type in ('all', 'series'):
        series_q = Series.query.filter(
            Series.is_active == True,
            or_(
                Series.title.ilike(pattern),
                Series.synopsis.ilike(pattern),
                Series.original_title.ilike(pattern),
            )
        ).order_by(
            # Priorizar coincidencia exacta en título
            func.instr(func.lower(Series.title), query_str.lower()).desc(),
            desc(Series.rating_avg),
        ).limit(limit)

        series_results = [_series_brief(s) for s in series_q.all()]

    if filter_type in ('all', 'movie'):
        movies_q = Movie.query.filter(
            Movie.is_active == True,
            or_(
                Movie.title.ilike(pattern),
                Movie.synopsis.ilike(pattern),
                Movie.original_title.ilike(pattern),
            )
        ).order_by(
            func.instr(func.lower(Movie.title), query_str.lower()).desc(),
            desc(Movie.rating_avg),
        ).limit(limit)

        movie_results = [_movie_brief(m) for m in movies_q.all()]

    return jsonify({
        'query':  query_str,
        'total':  len(series_results) + len(movie_results),
        'series': series_results,
        'movies': movie_results,
    })


# ─── 3. CONTENIDO DESTACADO ───────────────────────────────────────────────────

@bp.route('/content/featured')
@cache.cached(timeout=300)
def featured():
    """
    Contenido destacado para el Hero de la homepage.
    Retorna entre 3 y 8 items mezclando series y películas destacadas.
    """
    featured_series = Series.query.filter(
        Series.is_active == True,
        Series.is_featured == True,
    ).order_by(desc(Series.created_at)).limit(4).all()

    featured_movies = Movie.query.filter(
        Movie.is_active == True,
        Movie.is_featured == True,
    ).order_by(desc(Movie.created_at)).limit(4).all()

    # Si no hay contenido destacado, usar el más valorado
    if not featured_series and not featured_movies:
        featured_series = Series.query.filter(
            Series.is_active == True
        ).order_by(desc(Series.rating_avg)).limit(4).all()

        featured_movies = Movie.query.filter(
            Movie.is_active == True
        ).order_by(desc(Movie.rating_avg)).limit(4).all()

    items = []
    for s in featured_series:
        items.append({**_series_brief(s), 'synopsis': s.synopsis or ''})
    for m in featured_movies:
        items.append({**_movie_brief(m), 'synopsis': m.synopsis or '', 'duration': m.duration})

    return jsonify({'featured': items, 'count': len(items)})


# ─── 4. TENDENCIAS ────────────────────────────────────────────────────────────

@bp.route('/content/trending')
@cache.cached(timeout=300)
def trending():
    """
    Contenido en tendencia: más visto y mejor valorado últimamente.
    """
    limit = min(int(request.args.get('limit', 20)), 50)

    # Series con más historial de visualización reciente
    trending_series = db.session.query(Series).join(
        Episode, Episode.series_id == Series.id
    ).join(
        WatchHistory,
        WatchHistory.episode_id == Episode.id,
        isouter=True
    ).filter(
        Series.is_active == True,
        WatchHistory.watched_at >= since
    ).group_by(Series.id).order_by(
        desc(func.count(WatchHistory.id)),
        desc(Series.rating_avg)
    ).limit(limit // 2).all()

    trending_movies = db.session.query(Movie).join(
        WatchHistory,
        WatchHistory.movie_id == Movie.id,
        isouter=True
    ).filter(
        Movie.is_active == True
    ).group_by(Movie.id).order_by(
        desc(func.count(WatchHistory.id)),
        desc(Movie.rating_avg)
    ).limit(limit // 2).all()

    # Si no hay historial, usar más valorados
    if not trending_series:
        trending_series = Series.query.filter(
            Series.is_active == True
        ).order_by(desc(Series.rating_avg)).limit(limit // 2).all()

    if not trending_movies:
        trending_movies = Movie.query.filter(
            Movie.is_active == True
        ).order_by(desc(Movie.rating_avg)).limit(limit // 2).all()

    return jsonify({
        'series': [_series_brief(s) for s in trending_series],
        'movies': [_movie_brief(m) for m in trending_movies],
    })



# ─── 5. CONTENIDO RECIENTE ────────────────────────────────────────────────────

@bp.route('/content/recent')
def recent():
    """Últimas series y películas añadidas."""
    limit = min(int(request.args.get('limit', 16)), 40)

    recent_series = Series.query.filter(
        Series.is_active == True
    ).order_by(desc(Series.created_at)).limit(limit).all()

    recent_movies = Movie.query.filter(
        Movie.is_active == True
    ).order_by(desc(Movie.created_at)).limit(limit).all()

    return jsonify({
        'series': [_series_brief(s) for s in recent_series],
        'movies': [_movie_brief(m) for m in recent_movies],
    })


# ─── 6. DETALLE DE SERIE ──────────────────────────────────────────────────────

@bp.route('/series/<int:series_id>')
def series_detail(series_id):
    """Detalle completo de una serie incluyendo temporadas y episodios."""
    series = Series.query.filter_by(id=series_id, is_active=True).first_or_404()

    seasons_data = []
    for season in sorted(series.seasons, key=lambda s: s.number):
        episodes_data = []
        for ep in sorted(season.episodes, key=lambda e: e.number):
            episodes_data.append({
                'id': ep.id, 'number': ep.number, 'title': ep.title,
                'synopsis': ep.synopsis, 'duration': ep.duration,
                'thumbnail_url': ep.thumbnail_url,
                'video_url': ep.video_url if current_user.is_authenticated else None,
                'air_date': ep.air_date.isoformat() if ep.air_date else None,
            })
        seasons_data.append({
            'id': season.id, 'number': season.number,
            'title': season.title or f'Temporada {season.number}',
            'episode_count': season.episode_count,
            'episodes': episodes_data,
        })

    # Progreso del usuario en esta serie
    user_progress = {}
    if current_user.is_authenticated:
        history = WatchHistory.query.join(Episode).filter(
            WatchHistory.user_id == current_user.id, Episode.series_id == series_id
        ).order_by(desc(WatchHistory.watched_at)).first()
        if history:
            user_progress = {
                'episode_id':     history.episode_id,
                'progress':       history.progress,
                'progress_pct':   history.progress_percentage,
                'last_watched':   history.watched_at.isoformat() if history.watched_at else None,
            }

    return jsonify({
        'id': series.id, 'title': series.title,
        'original_title': series.original_title,
        'slug': series.slug, 'synopsis': series.synopsis,
        'cover_url': series.cover_url, 'banner_url': series.banner_url,
        'year': series.year, 'status': series.status,
        'rating_avg': float(series.rating_avg) if series.rating_avg else None,
        'rating_count': series.rating_count,
        'categories': [{'id': c.id, 'name': c.name} for c in series.categories],
        'seasons': seasons_data,
        'season_count': series.season_count,
        'episode_count': series.episode_count,
        'is_favorite': _is_favorite('series', series.id),
        'user_progress': user_progress,
    })


# ─── 7. DETALLE DE PELÍCULA ───────────────────────────────────────────────────

@bp.route('/movies/<int:movie_id>')
def movie_detail(movie_id):
    """Detalle completo de una película."""
    movie = Movie.query.filter_by(id=movie_id, is_active=True).first_or_404()

    # Progreso del usuario
    user_progress = {}
    if current_user.is_authenticated:
        history = WatchHistory.query.filter_by(
            user_id=current_user.id, movie_id=movie_id
        ).first()
        if history:
            user_progress = {
                'progress':     history.progress,
                'progress_pct': history.progress_percentage,
            }

    return jsonify({
        'id': movie.id, 'title': movie.title,
        'original_title': movie.original_title,
        'slug': movie.slug, 'synopsis': movie.synopsis,
        'cover_url': movie.cover_url, 'banner_url': movie.banner_url,
        'year': movie.year, 'duration': movie.duration,
        'video_url': movie.video_url if current_user.is_authenticated else None,
        'rating_avg': float(movie.rating_avg) if movie.rating_avg else None,
        'rating_count': movie.rating_count,
        'categories': [{'id': c.id, 'name': c.name} for c in movie.categories],
        'is_favorite': _is_favorite('movie', movie.id),
        'user_progress': user_progress,
    })


# ─── 8. FAVORITOS ────────────────────────────────────────────────────────────

@bp.route('/favorites/toggle', methods=['POST'])
@api_login_required
def toggle_favorite():
    """
    Añadir o quitar un elemento de favoritos.
    Body JSON: { "type": "series"|"movie", "id": <int> }
    """
    data         = request.get_json(silent=True) or {}
    content_type = data.get('type')
    content_id   = data.get('id')

    if content_type not in ('series', 'movie') or not content_id:
        return jsonify({'error': 'Parámetros inválidos'}), 400

    # Verificar que el contenido existe
    if content_type == 'series':
        content = Series.query.filter_by(id=content_id, is_active=True).first()
    else:
        content = Movie.query.filter_by(id=content_id, is_active=True).first()

    if not content:
        return jsonify({'error': 'Contenido no encontrado'}), 404

    # Buscar favorito existente
    q = Favorite.query.filter_by(user_id=current_user.id)
    if content_type == 'series':
        existing = q.filter_by(series_id=content_id).first()
    else:
        existing = q.filter_by(movie_id=content_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'added': False, 'message': 'Eliminado de favoritos'})
    else:
        fav = Favorite(user_id=current_user.id)
        if content_type == 'series':
            fav.series_id = content_id
        else:
            fav.movie_id = content_id
        db.session.add(fav)
        db.session.commit()
        return jsonify({'added': True, 'message': 'Añadido a favoritos'})


@bp.route('/favorites')
@api_login_required
def get_favorites():
    """Obtener lista de favoritos del usuario autenticado."""
    page     = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 24)), 100)

    favs = Favorite.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(Favorite.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    items = []
    for fav in favs.items:
        if fav.series:
            items.append(_series_brief(fav.series))
        elif fav.movie:
            items.append(_movie_brief(fav.movie))

    return jsonify({
        'items':    items,
        'total':    favs.total,
        'page':     favs.page,
        'pages':    favs.pages,
        'has_next': favs.has_next,
    })


# ─── 9. HISTORIAL Y PROGRESO ─────────────────────────────────────────────────

@bp.route('/history/update', methods=['POST'])
@api_login_required
def update_history():
    """
    Actualizar progreso de visualización.
    Body JSON: {
        "type": "series"|"movie",
        "id": <content_id>,
        "episode_id": <episode_id>,  # Solo para series
        "progress": <segundos_vistos>,
        "duration": <duración_total>
    }
    """
    data         = request.get_json(silent=True) or {}
    content_type = data.get('type')
    content_id   = int(data.get('id', 0))
    progress     = int(data.get('progress', 0))
    duration     = int(data.get('duration', 0))
    episode_id   = data.get('episode_id')

    if content_type not in ('series', 'movie') or not content_id:
        return jsonify({'error': 'Parámetros inválidos'}), 400

    # Buscar historial existente o crear nuevo
    q = WatchHistory.query.filter_by(user_id=current_user.id)
    if content_type == 'series':
        entry = q.filter_by(episode_id=episode_id).first()
    else:
        entry = q.filter_by(movie_id=content_id).first()

    if entry:
        entry.progress   = progress
        entry.duration   = duration or entry.duration
        entry.watched_at = datetime.now(timezone.utc)
    else:
        entry = WatchHistory(
            user_id=current_user.id,
            progress=progress,
            duration=duration,
            watched_at=datetime.now(timezone.utc),
        )
        if content_type == 'series':
            entry.episode_id = episode_id
        else:
            entry.movie_id = content_id
        db.session.add(entry)

    db.session.commit()
    return jsonify({'ok': True, 'progress': progress})


@bp.route('/history')
@api_login_required
def get_history():
    """Obtener historial de visualización del usuario."""
    limit = min(int(request.args.get('limit', 20)), 100)

    history = WatchHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(WatchHistory.watched_at)).limit(limit).all()

    items = []
    for h in history:
        item = {
            'progress':     h.progress,
            'progress_pct': h.progress_percentage,
            'watched_at':   h.watched_at.isoformat() if h.watched_at else None,
        }
        if h.series:
            item.update(_series_brief(h.series))
            item['episode_id'] = h.episode_id
        elif h.movie:
            item.update(_movie_brief(h.movie))
        items.append(item)

    return jsonify({'items': items, 'total': len(items)})


# ─── 10. VALORACIONES ─────────────────────────────────────────────────────────

@bp.route('/ratings', methods=['POST'])
@api_login_required
@limiter.limit('30 per hour')
def rate_content():
    """
    Valorar una serie o película.
    Body JSON: { "type": "series"|"movie", "id": <int>, "score": <1-10> }
    """
    data         = request.get_json(silent=True) or {}
    content_type = data.get('type')
    content_id   = data.get('id')
    score        = data.get('score')

    if content_type not in ('series', 'movie') or not content_id:
        return jsonify({'error': 'Parámetros inválidos'}), 400

    try:
        score = int(score)
        if not 1 <= score <= 10:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'La valoración debe ser un número entre 1 y 10'}), 400

    # Buscar valoración existente o crear nueva
    q = Rating.query.filter_by(user_id=current_user.id)
    if content_type == 'series':
        existing = q.filter_by(series_id=content_id).first()
    else:
        existing = q.filter_by(movie_id=content_id).first()

    if existing:
        existing.score = score
    else:
        rating = Rating(user_id=current_user.id, score=score)
        if content_type == 'series':
            rating.series_id = content_id
        else:
            rating.movie_id = content_id
        db.session.add(rating)

    db.session.commit()

    # Recalcular el promedio en el modelo
    if content_type == 'series':
        content = Series.query.get(content_id)
    else:
        content = Movie.query.get(content_id)

    if content:
        avg = db.session.query(func.avg(Rating.score)).filter(
            Rating.series_id == content_id if content_type == 'series'
            else Rating.movie_id == content_id
        ).scalar()
        count = db.session.query(func.count(Rating.id)).filter(
            Rating.series_id == content_id if content_type == 'series'
            else Rating.movie_id == content_id
        ).scalar()
        content.rating_avg   = round(float(avg), 2) if avg else None
        content.rating_count = count or 0
        db.session.commit()

    return jsonify({'ok': True, 'score': score})


# ─── 11. CATEGORÍAS ──────────────────────────────────────────────────────────

@bp.route('/categories')
def categories():
    """Listar todas las categorías activas con conteo de contenido."""
    cats = Category.query.filter_by(is_active=True).order_by(Category.order).all()

    result = []
    for cat in cats:
        series_count = db.session.query(func.count()).select_from(
            Series
        ).join(Series.categories).filter(
            Category.id == cat.id, Series.is_active == True
        ).scalar() or 0

        movie_count = db.session.query(func.count()).select_from(
            Movie
        ).join(Movie.categories).filter(
            Category.id == cat.id, Movie.is_active == True
        ).scalar() or 0

        result.append({
            'id':           cat.id,
            'name':         cat.name,
            'slug':         cat.slug,
            'color':        cat.color,
            'icon':         cat.icon,
            'series_count': series_count,
            'movie_count':  movie_count,
            'total':        series_count + movie_count,
        })

    return jsonify({'categories': result, 'total': len(result)})
