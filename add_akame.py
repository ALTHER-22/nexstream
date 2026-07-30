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
        series = Series.query.filter(Series.title.ilike('%Akame ga Kill%')).first()
        
        if not series:
            print("Creando la serie 'Akame ga Kill' en la base de datos...")
            series = Series(
                title='Akame ga Kill!',
                original_title='Akame ga Kiru!',
                slug='akame-ga-kill',
                synopsis='Tatsumi es un joven que viaja a la capital del Imperio para alistarse en el ejército. Sin embargo, descubre que la ciudad es un nido de corrupción y maldad. Tras ser rescatado por Night Raid, un grupo de asesinos rebeldes, decide unirse a ellos para acabar con la tiranía del Imperio.',
                year=2014,
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
                title='La Serie Completa (Cap 1-24)',
                description='Recopilación de los 24 capítulos de Akame ga Kill!',
                video_url='https://ok.ru/videoembed/14537217215214'
            )
            db.session.add(episode)
            db.session.commit()
            print("¡Serie Akame ga Kill y video añadidos con éxito!")
        else:
            episode.video_url = 'https://ok.ru/videoembed/14537217215214'
            db.session.commit()
            print("El video ha sido actualizado en el episodio 1.")

if __name__ == '__main__':
    run()
