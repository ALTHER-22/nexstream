"""
=============================================================================
NEXSTREAM — Rutas del CMS de Administración
=============================================================================
Archivo: app/admin/routes.py
Descripción: Gestión de contenido (CRUD) para Series, Películas y Episodios.
=============================================================================
"""

import os
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func

from extensions import db
from app.admin import bp
from app.admin.forms import SeriesForm, MovieForm, SeasonForm, EpisodeForm, CategoryForm
from app.models import User, Series, Movie, Category, Subscription, ActivityLog

# ─── UTILIDADES DE IMAGEN (PILLOW) ────────────────────────────────────────

def _save_image(upload, folder_name, target_size=None):
    """
    Guarda una imagen optimizada usando Pillow.
    Retorna la URL relativa para guardar en BD.
    """
    if not upload or not hasattr(upload, 'filename') or not upload.filename:
        return None
        
    from PIL import Image
    import secrets
    from werkzeug.utils import secure_filename
    
    random_hex = secrets.token_hex(8)
    raw_ext = os.path.splitext(secure_filename(upload.filename))[1].lower()
    
    # Asegurar directorio
    base_dir = os.path.join(current_app.root_path, 'static', 'uploads', folder_name)
    os.makedirs(base_dir, exist_ok=True)
    
    try:
        img = Image.open(upload)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        if target_size:
            from PIL import ImageOps
            img = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
            
        # Intentar guardar como WEBP, con fallback a JPG/PNG
        try:
            filename = random_hex + '.webp'
            filepath = os.path.join(base_dir, filename)
            img.save(filepath, format='WEBP', quality=85, optimize=True)
            return filename
        except Exception:
            ext = 'png' if raw_ext == '.png' else 'jpg'
            filename = random_hex + '.' + ext
            filepath = os.path.join(base_dir, filename)
            fmt = 'PNG' if ext == 'png' else 'JPEG'
            img.save(filepath, format=fmt, quality=85)
            return filename
    except Exception as e:
        current_app.logger.error(f"Error procesando imagen: {e}")
        return None

    try:
        if old_filename:
            old_path = os.path.join(base_dir, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
    except Exception as e:
        current_app.logger.error(f"Error borrando imagen antigua {old_filename}: {e}")

def _clean_video_url(url):
    """
    Extrae el atributo src si el usuario pega un iframe completo por error.
    """
    if not url:
        return url
    
    url = url.strip()
    if '<iframe' in url.lower():
        import re
        match = re.search(r'src=["\']([^"\']+)["\']', url, re.IGNORECASE)
        if match:
            url = match.group(1).strip()
            
    if url.startswith('//'):
        url = 'https:' + url
        
    return url

# ─── MIDDLEWARE Y LOGGING ──────────────────────────────────────────────────

def admin_required(f):
    """Decorador: Asegura que el usuario sea administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ─── DASHBOARD ─────────────────────────────────────────────────────────────

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Panel principal con métricas globales."""
    stats = {
        'total_users': User.query.count(),
        'total_series': Series.query.count(),
        'total_movies': Movie.query.count(),
        'active_subscriptions': Subscription.query.filter_by(status='active').count(),
    }
    
    # Última actividad
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_activity=recent_activity,
        title='Dashboard Admin — NEXSTREAM'
    )


# ─── GESTIÓN DE SERIES ─────────────────────────────────────────────────────

@bp.route('/series')
@login_required
@admin_required
def list_series():
    """Listado de todas las series."""
    page = request.args.get('page', 1, type=int)
    series_q = Series.query.order_by(Series.created_at.desc())
    pagination = series_q.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/series/index.html', pagination=pagination, title='Gestión de Series')


@bp.route('/series/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def create_series():
    """Crear una nueva serie."""
    form = SeriesForm()
    # Llenar opciones de categorías
    form.categories.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    
    if form.validate_on_submit():
        serie = Series(
            title=form.title.data,
            original_title=form.original_title.data,
            slug=form.slug.data,
            synopsis=form.synopsis.data,
            year=form.year.data,
            status=form.status.data,
            is_active=form.is_active.data
        )
        
        # Asignar categorías
        selected_cats = Category.query.filter(Category.id.in_(form.categories.data or [])).all()
        serie.categories = selected_cats
        
        db.session.add(serie)
        db.session.commit()
        
        # Procesar imágenes
        if form.cover.data and form.cover.data.filename:
            saved = _save_image(form.cover.data, 'covers', (600, 900))
            if saved:
                serie.cover = saved
        if form.banner.data and form.banner.data.filename:
            saved = _save_image(form.banner.data, 'banners', (1920, 1080))
            if saved:
                serie.banner = saved
        db.session.commit()
            
        flash(f'Serie "{serie.title}" creada correctamente.', 'success')
        return redirect(url_for('admin.list_series'))
        
    return render_template('admin/series/form.html', form=form, title='Nueva Serie')


@bp.route('/series/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_series(id):
    """Editar una serie existente."""
    serie = Series.query.get_or_404(id)
    form = SeriesForm(obj=serie)
    form.categories.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    
    if request.method == 'GET':
        form.categories.data = [c.id for c in serie.categories]
        
    if form.validate_on_submit():
        old_cover = serie.cover
        old_banner = serie.banner
        
        # Evitar que populate_obj intente poblar 'categories' con lista de enteros
        categories_field = form._fields.pop('categories', None)
        form.populate_obj(serie)
        if categories_field:
            form._fields['categories'] = categories_field
        
        serie.cover = old_cover
        serie.banner = old_banner
        
        if request.files.get('cover') and request.files['cover'].filename:
            saved = _save_image(request.files['cover'], 'covers', (600, 900))
            if saved:
                serie.cover = saved
        if request.files.get('banner') and request.files['banner'].filename:
            saved = _save_image(request.files['banner'], 'banners', (1920, 1080))
            if saved:
                serie.banner = saved
            
        selected_cats = Category.query.filter(Category.id.in_(form.categories.data or [])).all()
        serie.categories = selected_cats
        
        db.session.commit()
        flash(f'Serie "{serie.title}" actualizada.', 'success')
        return redirect(url_for('admin.list_series'))
        
    return render_template('admin/series/form.html', form=form, serie=serie, title=f'Editar: {serie.title}')
    

@bp.route('/series/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_series(id):
    """Eliminar una serie."""
    serie = Series.query.get_or_404(id)
    db.session.delete(serie)
    db.session.commit()
    flash(f'Serie "{serie.title}" eliminada.', 'success')
    return redirect(url_for('admin.list_series'))


# ─── GESTIÓN DE PELÍCULAS ──────────────────────────────────────────────────

@bp.route('/peliculas')
@login_required
@admin_required
def list_movies():
    """Listado de todas las películas."""
    page = request.args.get('page', 1, type=int)
    movies_q = Movie.query.order_by(Movie.created_at.desc())
    pagination = movies_q.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/movies/index.html', pagination=pagination, title='Gestión de Películas')


@bp.route('/peliculas/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def create_movie():
    """Crear una nueva película."""
    form = MovieForm()
    form.categories.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    
    if form.validate_on_submit():
        movie = Movie(
            title=form.title.data,
            original_title=form.original_title.data,
            slug=form.slug.data,
            synopsis=form.synopsis.data,
            year=form.year.data,
            duration=form.duration.data,
            video_url=form.video_url.data,
            is_active=form.is_active.data
        )
        
        selected_cats = Category.query.filter(Category.id.in_(form.categories.data or [])).all()
        movie.categories = selected_cats
        
        # Procesar imágenes
        if form.cover.data and form.cover.data.filename:
            saved = _save_image(form.cover.data, 'covers', (600, 900))
            if saved:
                movie.cover = saved
        if form.banner.data and form.banner.data.filename:
            saved = _save_image(form.banner.data, 'banners', (1920, 1080))
            if saved:
                movie.banner = saved
            
        db.session.add(movie)
        db.session.commit()
        
        flash(f'Película "{movie.title}" creada correctamente.', 'success')
        return redirect(url_for('admin.list_movies'))
        
    return render_template('admin/movies/form.html', form=form, title='Nueva Película')

@bp.route('/peliculas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_movie(id):
    """Editar una película existente."""
    movie = Movie.query.get_or_404(id)
    form = MovieForm(obj=movie)
    form.categories.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    
    if request.method == 'GET':
        form.categories.data = [c.id for c in movie.categories]
        
    if form.validate_on_submit():
        old_cover = movie.cover
        old_banner = movie.banner
        
        # Evitar que populate_obj intente poblar 'categories' con lista de enteros
        categories_field = form._fields.pop('categories', None)
        form.populate_obj(movie)
        if categories_field:
            form._fields['categories'] = categories_field
        
        movie.cover = old_cover
        movie.banner = old_banner
        
        if request.files.get('cover') and request.files['cover'].filename:
            saved = _save_image(request.files['cover'], 'covers', (600, 900))
            if saved:
                movie.cover = saved
        if request.files.get('banner') and request.files['banner'].filename:
            saved = _save_image(request.files['banner'], 'banners', (1920, 1080))
            if saved:
                movie.banner = saved

        selected_cats = Category.query.filter(Category.id.in_(form.categories.data or [])).all()
        movie.categories = selected_cats
        db.session.commit()
        
        flash(f'Película "{movie.title}" actualizada.', 'success')
        return redirect(url_for('admin.list_movies'))
        
    return render_template('admin/movies/form.html', form=form, movie=movie, title=f'Editar: {movie.title}')


@bp.route('/peliculas/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_movie(id):
    """Eliminar una película."""
    movie = Movie.query.get_or_404(id)
    db.session.delete(movie)
    db.session.commit()
    flash(f'Película "{movie.title}" eliminada.', 'success')
    return redirect(url_for('admin.list_movies'))


# ─── GESTIÓN DE EPISODIOS ──────────────────────────────────────────────────

@bp.route('/series/<int:series_id>/episodios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def create_episode(series_id):
    """Añadir un episodio a una serie (y crear la temporada si es necesario)."""
    from app.models import Season, Episode
    serie = Series.query.get_or_404(series_id)
    form = EpisodeForm()
    
    # Podríamos añadir un SeasonForm aquí, pero para simplificar, 
    # pedimos la temporada como un simple entero por query param o asumimos T1.
    season_number = request.args.get('season', 1, type=int)
    
    if form.validate_on_submit():
        # Buscar o crear la temporada
        season = Season.query.filter_by(series_id=serie.id, number=season_number).first()
        if not season:
            season = Season(series_id=serie.id, number=season_number, title=f"Temporada {season_number}")
            db.session.add(season)
            db.session.commit()
            
        episode = Episode(
            season_id=season.id,
            number=form.number.data,
            title=form.title.data,
            synopsis=form.synopsis.data,
            duration=form.duration.data,
            video_url=form.video_url.data,
            air_date=form.air_date.data
        )
        # Procesar miniatura
        if form.thumbnail.data and form.thumbnail.data.filename:
            episode.thumbnail = _save_image(form.thumbnail.data, 'thumbnails', (1280, 720))
            
        db.session.add(episode)
        db.session.commit()
        
        flash(f'Episodio {episode.number} añadido a la Temporada {season.number}.', 'success')
        return redirect(url_for('admin.list_series'))
        
    return render_template('admin/series/episode_form.html', form=form, serie=serie, season_num=season_number)


# ─── GESTIÓN DE CATEGORÍAS ─────────────────────────────────────────────────

@bp.route('/categorias')
@login_required
@admin_required
def list_categories():
    """Listado de categorías."""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories/index.html', categories=categories, title='Gestión de Categorías')

@bp.route('/categorias/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """Crear nueva categoría."""
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, slug=form.slug.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash(f'Categoría "{category.name}" creada.', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/categories/form.html', form=form, title='Nueva Categoría')

@bp.route('/categorias/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    """Editar categoría."""
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash(f'Categoría "{category.name}" actualizada.', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/categories/form.html', form=form, category=category, title=f'Editar: {category.name}')

@bp.route('/categorias/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    """Eliminar categoría."""
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash(f'Categoría eliminada.', 'success')
    return redirect(url_for('admin.list_categories'))


# ─── GESTIÓN DE USUARIOS ───────────────────────────────────────────────────

@bp.route('/usuarios')
@login_required
@admin_required
def list_users():
    """Listado de usuarios."""
    page = request.args.get('page', 1, type=int)
    users_q = User.query.order_by(User.created_at.desc())
    pagination = users_q.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users/index.html', pagination=pagination, title='Gestión de Usuarios')

@bp.route('/usuarios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Eliminar usuario."""
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'error')
        return redirect(url_for('admin.list_users'))
        
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario {user.username} eliminado.', 'success')
    return redirect(url_for('admin.list_users'))
