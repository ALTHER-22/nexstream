"""
=============================================================================
NEXSTREAM — Rutas Principales (Catálogo y Páginas de Contenido)
=============================================================================
Archivo: app/main/routes.py
Descripción: Rutas del catálogo público de NEXSTREAM.

Páginas:
  /                    — Home con hero, tendencias y sliders
  /catalogo            — Catálogo completo con filtros y paginación
  /serie/<slug>        — Detalle de serie
  /pelicula/<slug>     — Detalle de película
  /categoria/<slug>    — Contenido por categoría
  /buscar              — Página de resultados de búsqueda
=============================================================================
"""

from flask import (
    render_template, request, redirect,
    url_for, abort, jsonify, current_app
)
from flask_login import current_user
from sqlalchemy import desc, or_, func
from extensions import db
from app.main import bp
from app.models.content import Series, Movie, Category, Episode, Season, Banner
from app.models.interaction import WatchHistory, Favorite


# ─── HOME ────────────────────────────────────────────────────────────────────

@bp.route('/')
@bp.route('/index')
def index():
    """
    Página principal de NEXSTREAM.
    Muestra hero, contenido destacado, tendencias y sliders por categoría.
    """
    # Banners del hero
    # Banners del hero generados a partir de contenido real
    hero_banners = []
    
    from sqlalchemy.orm import joinedload

    # 3 mejores series
    top_series = Series.query.filter_by(is_active=True).options(joinedload(Series.categories)).order_by(desc(Series.rating_avg)).limit(3).all()
    for s in top_series:
        hero_banners.append({
            'title': s.title,
            'description': s.synopsis,
            'image_url': s.banner_url,
            'cover_url': s.cover_url,
            'content_type': 'series',
            'year': s.year,
            'rating': s.rating_avg,
            'categories': ', '.join([c.name for c in s.categories]) if s.categories else '',
            'url': url_for('main.series_detail', series_id=s.id, slug=s.slug)
        })
        
    # 2 mejores películas
    top_movies = Movie.query.filter_by(is_active=True).options(joinedload(Movie.categories)).order_by(desc(Movie.rating_avg)).limit(2).all()
    for m in top_movies:
        hero_banners.append({
            'title': m.title,
            'description': m.synopsis,
            'image_url': m.banner_url,
            'cover_url': m.cover_url,
            'content_type': 'movie',
            'year': m.year,
            'rating': m.rating_avg,
            'categories': ', '.join([c.name for c in m.categories]) if m.categories else '',
            'url': url_for('main.play_movie', movie_id=m.id, slug=m.slug),
            'video_url': m.video_url
        })

    # Tendencias: Series
    trending_series = Series.query.filter_by(
        is_active=True
    ).order_by(desc(Series.rating_avg), desc(Series.rating_count)).limit(12).all()

    # Tendencias: Películas
    trending_movies = Movie.query.filter_by(
        is_active=True
    ).order_by(desc(Movie.rating_avg), desc(Movie.rating_count)).limit(12).all()

    # Recién añadidas
    recent_series = Series.query.filter_by(
        is_active=True
    ).order_by(desc(Series.created_at)).limit(12).all()

    recent_movies = Movie.query.filter_by(
        is_active=True
    ).order_by(desc(Movie.created_at)).limit(12).all()

    # Continuar viendo (solo usuarios autenticados)
    continue_watching = []
    recommended_for_you = []
    if current_user.is_authenticated:
        history = WatchHistory.query.filter(
            WatchHistory.user_id == current_user.id,
            WatchHistory.completed == False,
            WatchHistory.progress > 30,
        ).order_by(desc(WatchHistory.watched_at)).limit(8).all()
        continue_watching = history
        
        # Generar recomendaciones basadas en la última categoría vista
        last_history = WatchHistory.query.filter_by(user_id=current_user.id).order_by(desc(WatchHistory.watched_at)).first()
        if last_history:
            last_series = last_history.episode.season.series if last_history.episode and last_history.episode.season else None
            last_item = last_series or last_history.movie
            if last_item and last_item.categories:
                last_cat = last_item.categories[0]
                rec_series = Series.query.join(Series.categories).filter(
                    Category.id == last_cat.id,
                    Series.is_active == True,
                    Series.id != (last_item.id if last_series else 0)
                ).order_by(desc(Series.rating_avg)).limit(6).all()
                
                rec_movies = Movie.query.join(Movie.categories).filter(
                    Category.id == last_cat.id,
                    Movie.is_active == True,
                    Movie.id != (last_item.id if last_history.movie else 0)
                ).order_by(desc(Movie.rating_avg)).limit(6).all()
                
                recommended_for_you = (rec_series + rec_movies)[:12]

    # Categorías para la barra de navegación y sliders
    categories = Category.query.filter_by(
        is_active=True
    ).order_by(Category.order).limit(8).all()

    # Slider por categoría: tomar la primera con suficiente contenido
    category_sliders = []
    for cat in categories[:3]:
        cat_series = Series.query.join(Series.categories).filter(
            Category.id == cat.id,
            Series.is_active == True,
        ).order_by(desc(Series.rating_avg)).limit(8).all()

        cat_movies = Movie.query.join(Movie.categories).filter(
            Category.id == cat.id,
            Movie.is_active == True,
        ).order_by(desc(Movie.rating_avg)).limit(12).all()

        combined = cat_series + cat_movies
        if combined:
            category_sliders.append({
                'category': cat,
                'items':    combined[:16],
            })

    return render_template(
        'main/index.html',
        hero_banners      = hero_banners,
        trending_series   = trending_series,
        trending_movies   = trending_movies,
        recent_series     = recent_series,
        recent_movies     = recent_movies,
        continue_watching = continue_watching,
        recommended_for_you= recommended_for_you,
        categories        = categories,
        category_sliders  = category_sliders,
        title             = 'NEXSTREAM — Tu universo de entretenimiento',
    )


# ─── CATÁLOGO ────────────────────────────────────────────────────────────────

@bp.route('/catalogo')
def catalog():
    """
    Catálogo completo con filtros y paginación.
    Filtros: tipo, categoría, año, orden.
    """
    # Parámetros de filtro desde URL
    page       = max(1, int(request.args.get('page', 1)))
    per_page   = 24
    tipo       = request.args.get('tipo', 'all')   # all | series | movies
    cat_slug   = request.args.get('categoria', '')
    year       = request.args.get('anio', '')
    orden      = request.args.get('orden', 'reciente')  # reciente | titulo | rating
    q          = request.args.get('q', '').strip()

    categories  = Category.query.filter_by(is_active=True).order_by(Category.order).all()
    active_cat  = Category.query.filter_by(slug=cat_slug).first() if cat_slug else None

    # ── Query de Series ──
    series_q = Series.query.filter_by(is_active=True)
    if active_cat:
        series_q = series_q.join(Series.categories).filter(Category.id == active_cat.id)
    if year:
        series_q = series_q.filter(Series.year == int(year))
    if q:
        series_q = series_q.filter(
            or_(Series.title.ilike(f'%{q}%'), Series.synopsis.ilike(f'%{q}%'))
        )

    # ── Query de Películas ──
    movies_q = Movie.query.filter_by(is_active=True)
    if active_cat:
        movies_q = movies_q.join(Movie.categories).filter(Category.id == active_cat.id)
    if year:
        movies_q = movies_q.filter(Movie.year == int(year))
    if q:
        movies_q = movies_q.filter(
            or_(Movie.title.ilike(f'%{q}%'), Movie.synopsis.ilike(f'%{q}%'))
        )

    # ── Orden ──
    order_map_series = {
        'reciente': desc(Series.created_at),
        'titulo':   Series.title,
        'rating':   desc(Series.rating_avg),
        'anio':     desc(Series.year),
    }
    order_map_movies = {
        'reciente': desc(Movie.created_at),
        'titulo':   Movie.title,
        'rating':   desc(Movie.rating_avg),
        'anio':     desc(Movie.year),
    }

    series_q = series_q.order_by(order_map_series.get(orden, desc(Series.created_at)))
    movies_q = movies_q.order_by(order_map_movies.get(orden, desc(Movie.created_at)))

    # ── Paginación según tipo ──
    series_items, movies_items, pagination = [], [], None

    if tipo == 'movies':
        pagination = movies_q.paginate(page=page, per_page=per_page, error_out=False)
        movies_items = pagination.items
    elif tipo == 'series':
        pagination = series_q.paginate(page=page, per_page=per_page, error_out=False)
        series_items = pagination.items
    else:
        # Mezclar series y películas
        all_series = series_q.all()
        all_movies = movies_q.all()
        combined   = all_series + all_movies
        total      = len(combined)
        start      = (page - 1) * per_page
        end        = start + per_page
        page_items = combined[start:end]
        series_items = [i for i in page_items if isinstance(i, Series)]
        movies_items = [i for i in page_items if isinstance(i, Movie)]
        # Paginación manual
        from math import ceil
        class FakePagination:
            def __init__(self):
                self.total    = total
                self.page     = page
                self.per_page = per_page
                self.pages    = ceil(total / per_page) if total else 1
                self.has_next = page < self.pages
                self.has_prev = page > 1
                self.next_num = page + 1 if self.has_next else None
                self.prev_num = page - 1 if self.has_prev else None
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if (num <= left_edge or
                        (self.page - left_current - 1 < num < self.page + right_current) or
                        num > self.pages - right_edge):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        pagination = FakePagination()

    # Años disponibles para el filtro
    years_series = db.session.query(Series.year).filter(
        Series.is_active == True, Series.year != None
    ).distinct().order_by(desc(Series.year)).limit(20).all()

    years_movies = db.session.query(Movie.year).filter(
        Movie.is_active == True, Movie.year != None
    ).distinct().order_by(desc(Movie.year)).limit(20).all()

    available_years = sorted(
        set([y[0] for y in years_series] + [y[0] for y in years_movies]),
        reverse=True
    )

    return render_template(
        'main/catalog.html',
        series_items     = series_items,
        movies_items     = movies_items,
        pagination       = pagination,
        categories       = categories,
        active_cat       = active_cat,
        tipo             = tipo,
        orden            = orden,
        year             = year,
        q                = q,
        available_years  = available_years,
        title            = 'Catálogo — NEXSTREAM',
    )


# ─── PÁGINAS DE SOPORTE Y LEGALES ───────────────────────────────────────────

@bp.route('/soporte/ayuda')
def help_center():
    return render_template('pages/help.html', title='Centro de Ayuda - NEXSTREAM')

@bp.route('/soporte/contacto')
def contact():
    return render_template('pages/contact.html', title='Contacto - NEXSTREAM')

@bp.route('/legal/privacidad')
def privacy():
    return render_template('pages/privacy.html', title='Política de Privacidad - NEXSTREAM')

@bp.route('/legal/terminos')
def terms():
    return render_template('pages/terms.html', title='Términos de Uso - NEXSTREAM')

@bp.route('/legal/cookies')
def cookies():
    return render_template('pages/cookies.html', title='Política de Cookies - NEXSTREAM')


# ─── DETALLE DE SERIE ─────────────────────────────────────────────────────────

@bp.route('/serie/<slug>')
def series_detail(slug):
    """Página de detalle de una serie."""
    series = Series.query.filter_by(slug=slug, is_active=True).first_or_404()

    # Ordenar temporadas
    seasons = sorted(series.seasons, key=lambda s: s.number)

    # Temporada activa (la última o la del progreso del usuario)
    active_season_num = 1
    current_episode   = None

    if current_user.is_authenticated:
        last_watch = WatchHistory.query.join(Episode).join(Season).filter(
            WatchHistory.user_id == current_user.id,
            Season.series_id == series.id
        ).order_by(desc(WatchHistory.watched_at)).first()
        if last_watch and last_watch.episode:
            active_season_num = last_watch.episode.season.number
            current_episode   = last_watch.episode

    active_season = next(
        (s for s in seasons if s.number == active_season_num),
        seasons[0] if seasons else None
    )

    # Comprobar si es favorito
    is_favorite = False
    user_rating = None
    if current_user.is_authenticated:
        from app.models.interaction import Rating
        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id, series_id=series.id
        ).first() is not None
        
        rating = Rating.query.filter_by(
            user_id=current_user.id, series_id=series.id
        ).first()
        if rating:
            user_rating = rating.score

    # Series relacionadas (misma categoría)
    related = []
    if series.categories:
        related = Series.query.join(Series.categories).filter(
            Category.id == series.categories[0].id,
            Series.id != series.id,
            Series.is_active == True,
        ).order_by(desc(Series.rating_avg)).limit(8).all()

    return render_template(
        'main/series_detail.html',
        series          = series,
        seasons         = seasons,
        active_season   = active_season,
        current_episode = current_episode,
        is_favorite     = is_favorite,
        user_rating     = user_rating,
        related         = related,
        title           = f'{series.title} — NEXSTREAM',
    )


# ─── DETALLE DE PELÍCULA ──────────────────────────────────────────────────────

@bp.route('/pelicula/<slug>')
def movie_detail(slug):
    """Página de detalle de una película."""
    movie = Movie.query.filter_by(slug=slug, is_active=True).first_or_404()

    # Progreso del usuario
    user_progress = None
    is_favorite   = False
    user_rating   = None

    if current_user.is_authenticated:
        from app.models.interaction import Rating
        history = WatchHistory.query.filter_by(
            user_id=current_user.id, movie_id=movie.id
        ).first()
        user_progress = history

        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id, movie_id=movie.id
        ).first() is not None
        
        rating = Rating.query.filter_by(
            user_id=current_user.id, movie_id=movie.id
        ).first()
        if rating:
            user_rating = rating.score

    # Películas relacionadas
    related = []
    if movie.categories:
        related = Movie.query.join(Movie.categories).filter(
            Category.id == movie.categories[0].id,
            Movie.id != movie.id,
            Movie.is_active == True,
        ).order_by(desc(Movie.rating_avg)).limit(8).all()

    return render_template(
        'main/movie_detail.html',
        movie         = movie,
        user_progress = user_progress,
        is_favorite   = is_favorite,
        user_rating   = user_rating,
        related       = related,
        title         = f'{movie.title} — NEXSTREAM',
    )


# ─── CATEGORÍA ────────────────────────────────────────────────────────────────

@bp.route('/categoria/<slug>')
def category(slug):
    """Página de contenido por categoría."""
    cat    = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    page   = max(1, int(request.args.get('page', 1)))
    tipo   = request.args.get('tipo', 'all')

    series_items = Series.query.join(Series.categories).filter(
        Category.id == cat.id, Series.is_active == True
    ).order_by(desc(Series.rating_avg)).all()

    movies_items = Movie.query.join(Movie.categories).filter(
        Category.id == cat.id, Movie.is_active == True
    ).order_by(desc(Movie.rating_avg)).all()

    return render_template(
        'main/category.html',
        category     = cat,
        series_items = series_items,
        movies_items = movies_items,
        tipo         = tipo,
        title        = f'{cat.name} — NEXSTREAM',
    )


# ─── BÚSQUEDA ─────────────────────────────────────────────────────────────────

@bp.route('/buscar')
def search():
    """Página completa de resultados de búsqueda."""
    q      = request.args.get('q', '').strip()
    page   = max(1, int(request.args.get('page', 1)))
    tipo   = request.args.get('tipo', 'all')

    series_results = []
    movies_results = []

    if len(q) >= 2:
        pattern = f'%{q}%'

        if tipo in ('all', 'series'):
            series_results = Series.query.filter(
                Series.is_active == True,
                or_(Series.title.ilike(pattern), Series.synopsis.ilike(pattern))
            ).order_by(desc(Series.rating_avg)).limit(40).all()

        if tipo in ('all', 'movies'):
            movies_results = Movie.query.filter(
                Movie.is_active == True,
                or_(Movie.title.ilike(pattern), Movie.synopsis.ilike(pattern))
            ).order_by(desc(Movie.rating_avg)).limit(40).all()

    return render_template(
        'main/search.html',
        q              = q,
        tipo           = tipo,
        series_results = series_results,
        movies_results = movies_results,
        total          = len(series_results) + len(movies_results),
        title          = f'Búsqueda: {q} — NEXSTREAM' if q else 'Buscar — NEXSTREAM',
    )


# ─── REPRODUCTOR ──────────────────────────────────────────────────────────────

@bp.route('/reproducir/serie/<int:episode_id>')
def play_episode(episode_id):
    """Reproductor de video para un episodio específico."""
    episode = Episode.query.get_or_404(episode_id)
    series = episode.season.series
    
    # Buscar siguiente episodio
    next_episode = Episode.query.filter_by(season_id=episode.season_id, number=episode.number + 1).first()
    if not next_episode:
        # Siguiente temporada, episodio 1
        next_season = next((s for s in series.seasons if s.number == episode.season.number + 1), None)
        if next_season and next_season.episodes:
            next_episode = next((e for e in next_season.episodes if e.number == 1), None)
            
    # Historial de progreso actual
    start_time = 0
    if current_user.is_authenticated:
        history = WatchHistory.query.filter_by(
            user_id=current_user.id, episode_id=episode.id
        ).first()
        if history and history.progress_percentage < 95:
            start_time = history.progress

    is_embed = False
    if episode.video_url and any(d in episode.video_url.lower() for d in ['ok.ru', 'youtube', 'youtu.be', 'vimeo', 'drive.google.com']):
        is_embed = True

    return render_template(
        'main/player.html',
        item=episode,
        parent=series,
        type='series',
        next_item=next_episode,
        start_time=start_time,
        is_embed=is_embed,
        autoplay_next=current_user.autoplay if current_user.is_authenticated else False,
        title=f'{series.title} - S{episode.season.number}E{episode.number}'
    )

@bp.route('/reproducir/pelicula/<int:movie_id>')
def play_movie(movie_id):
    """Reproductor de video para una película."""
    movie = Movie.query.get_or_404(movie_id)
    
    start_time = 0
    if current_user.is_authenticated:
        history = WatchHistory.query.filter_by(
            user_id=current_user.id, movie_id=movie.id
        ).first()
        if history and history.progress_percentage < 95:
            start_time = history.progress

    is_embed = False
    if movie.video_url and any(d in movie.video_url.lower() for d in ['ok.ru', 'youtube', 'youtu.be', 'vimeo', 'drive.google.com']):
        is_embed = True

    return render_template(
        'main/player.html',
        item=movie,
        type='movie',
        start_time=start_time,
        is_embed=is_embed,
        title=f'{movie.title} — Reproduciendo'
    )
