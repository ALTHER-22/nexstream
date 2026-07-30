import sys
try:
    from app import create_app
    from extensions import db
    from app.models.content import Series, Season, Episode, Category
except ImportError:
    import sys
    print("Por favor, ejecuta desde la carpeta nexstream.")
    sys.exit(1)

app = create_app()

def run():
    with app.app_context():
        # Buscar o crear categoría Anime
        category = Category.query.filter_by(name='Anime').first()
        if not category:
            category = Category(name='Anime', slug='anime')
            db.session.add(category)

        # Buscar si la serie ya existe
        series = Series.query.filter(Series.title.ilike('%Elfen Lied%')).first()
        
        if not series:
            print("Creando la serie 'Elfen Lied' en la base de datos...")
            series = Series(
                title='Elfen Lied',
                original_title='Elfen Lied',
                slug='elfen-lied',
                synopsis='Los Diclonius, una especie mutante con cuernos y poderes telequinéticos invisibles llamados "vectores", son mantenidos en cautiverio. Lucy, una Diclonius letal, escapa masacrando a los guardias pero sufre una lesión en la cabeza que la deja con una doble personalidad infantil llamada Nyu. Es acogida por dos estudiantes, Kouta y Yuka, sin saber que el gobierno ha desatado una cacería sangrienta para recuperarla.',
                year=2004,
                status='COMPLETED',
                is_active=True
            )
            series.categories.append(category)
            db.session.add(series)
            db.session.commit()
            print("Serie creada.")

        # 1. Crear o buscar Temporada 1
        season = Season.query.filter_by(series_id=series.id, number=1).first()
        if not season:
            season = Season(series_id=series.id, number=1, title='Temporada 1')
            db.session.add(season)
            db.session.commit()
            
        # 2. Crear Episodio
        episode = Episode.query.filter_by(season_id=season.id, number=1).first()
        if not episode:
            print("Añadiendo el video...")
            episode = Episode(
                season_id=season.id,
                number=1,
                title='La Serie Completa (Cap 1-13)',
                description='Recopilación de los 13 capítulos de Elfen Lied.',
                video_url='https://ok.ru/videoembed/10116989913838'
            )
            db.session.add(episode)
            db.session.commit()
            print("¡Serie Elfen Lied y video añadidos con éxito!")
        else:
            episode.video_url = 'https://ok.ru/videoembed/10116989913838'
            db.session.commit()
            print("El video ha sido actualizado en el episodio 1.")

if __name__ == '__main__':
    run()
