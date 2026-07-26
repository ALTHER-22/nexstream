"""
=============================================================================
NEXSTREAM — Formularios de Administración (CMS)
=============================================================================
Archivo: app/admin/forms.py
Descripción: Formularios WTForms para la gestión de contenido.
=============================================================================
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, BooleanField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import ListWidget, CheckboxInput


class MultiCheckboxField(SelectMultipleField):
    """Widget personalizado para mostrar SelectMultipleField como checkboxes."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class SeriesForm(FlaskForm):
    """Formulario para crear/editar Series."""
    
    title = StringField('Título', validators=[DataRequired(), Length(max=150)])
    original_title = StringField('Título Original', validators=[Optional(), Length(max=150)])
    slug = StringField('Slug (URL amigable)', validators=[DataRequired(), Length(max=150)])
    
    synopsis = TextAreaField('Sinopsis', validators=[Optional()])
    year = IntegerField('Año de lanzamiento', validators=[Optional(), NumberRange(min=1900, max=2100)])
    status = SelectField('Estado', choices=[
        ('ongoing', 'En emisión'), 
        ('ended', 'Finalizada'), 
        ('upcoming', 'Próximamente')
    ], default='ongoing')
    
    # Archivos
    cover = FileField('Imagen de Portada (Vertical 2:3)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'webp'])
    ])
    banner = FileField('Imagen de Banner (Horizontal 16:9)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'webp'])
    ])
    # Categorías (las opciones se llenan en la ruta)
    categories = MultiCheckboxField('Categorías', coerce=int)
    
    is_active = BooleanField('Publicado (Visible)', default=True)


class MovieForm(FlaskForm):
    """Formulario para crear/editar Películas."""
    
    title = StringField('Título', validators=[DataRequired(), Length(max=150)])
    original_title = StringField('Título Original', validators=[Optional(), Length(max=150)])
    slug = StringField('Slug (URL amigable)', validators=[DataRequired(), Length(max=150)])
    
    synopsis = TextAreaField('Sinopsis', validators=[Optional()])
    year = IntegerField('Año de lanzamiento', validators=[Optional(), NumberRange(min=1900, max=2100)])
    duration = IntegerField('Duración (minutos)', validators=[Optional(), NumberRange(min=1)])
    
    # Archivos
    cover = FileField('Imagen de Portada (Vertical 2:3)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'webp'])
    ])
    banner = FileField('Imagen de Banner (Horizontal 16:9)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'webp'])
    ])
    
    video_url = StringField('URL de la Película / HLS / MP4', validators=[Optional(), Length(max=255)])
    
    # Categorías
    categories = MultiCheckboxField('Categorías', coerce=int)
    
    is_active = BooleanField('Publicado (Visible)', default=True)


class SeasonForm(FlaskForm):
    """Formulario para gestionar Temporadas de una Serie."""
    number = IntegerField('Número de Temporada', validators=[DataRequired(), NumberRange(min=1)])
    title = StringField('Título (opcional)', validators=[Optional(), Length(max=100)])


class EpisodeForm(FlaskForm):
    """Formulario para añadir/editar Episodios."""
    number = IntegerField('Número de Episodio', validators=[DataRequired(), NumberRange(min=1)])
    title = StringField('Título del Episodio', validators=[Optional(), Length(max=150)])
    synopsis = TextAreaField('Sinopsis', validators=[Optional()])
    
    duration = IntegerField('Duración (minutos)', validators=[Optional(), NumberRange(min=1)])
    air_date = DateField('Fecha de emisión', format='%Y-%m-%d', validators=[Optional()])
    
    thumbnail = FileField('Miniatura del episodio (16:9)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'webp'])
    ])
    
    video_url = StringField('URL del Video / HLS / MP4', validators=[Optional(), Length(max=255)])


class CategoryForm(FlaskForm):
    """Formulario para añadir/editar Categorías."""
    name = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug (URL amigable)', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional()])
