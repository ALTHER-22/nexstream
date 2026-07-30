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
        series = Series.query.filter(Series.title.ilike('%Amos del Universo%')).first()
        
        if not series:
            print("Creando la serie 'Amos del Universo' en la base de datos...")
            series = Series(
                title='He-Man y los Amos del Universo',
                original_title='He-Man and the Masters of the Universe',
                slug='he-man-amos-del-universo',
                synopsis='El Príncipe Adam de Eternia recibe la Espada del Poder que lo transforma en He-Man, el hombre más poderoso del universo. Junto a sus aliados como Teela, Man-At-Arms y Orko, deberá defender el Castillo Grayskull y el planeta Eternia de las malvadas fuerzas de Skeletor y sus secuaces.',
                year=1983,
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
                title='La Serie Completa',
                description='Recopilación de capítulos de Amos del Universo.',
                video_url='https://ok.ru/videoembed/14769364798190'
            )
            db.session.add(episode)
            db.session.commit()
            print("¡Serie Amos del Universo y video añadidos con éxito!")
        else:
            episode.video_url = 'https://ok.ru/videoembed/14769364798190'
            db.session.commit()
            print("El video ha sido actualizado en el episodio 1.")

if __name__ == '__main__':
    run()
