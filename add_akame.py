import sys
try:
    from app import create_app
    from extensions import db
    from app.models.content import Series, Season, Episode
except ImportError:
    print("Por favor, ejecuta desde la carpeta nexstream.")
    sys.exit(1)

app = create_app()

def run():
    with app.app_context():
        # Buscar la serie de Akame ga Kill
        # Buscamos usando un filtro aproximado por si el nombre varía ("Akame ga Kill", "Akame ga Kill!", etc)
        series = Series.query.filter(Series.title.ilike('%Akame ga Kill%')).first()
        
        if not series:
            print("No se encontró la serie 'Akame ga Kill' en la base de datos.")
            print("Por favor crea la serie primero en el Panel de Administración.")
            return

        # 1. Crear o buscar Temporada 1
        season = Season.query.filter_by(series_id=series.id, number=1).first()
        if not season:
            season = Season(series_id=series.id, number=1, title='Temporada 1')
            db.session.add(season)
            db.session.commit()
            
        # 2. Crear Episodio (La animación completa o el video enviado)
        episode = Episode.query.filter_by(season_id=season.id, number=1).first()
        if not episode:
            print("Añadiendo el video a Akame ga Kill...")
            episode = Episode(
                season_id=season.id,
                number=1,
                title='La Serie Completa (Animación)',
                description='Recopilación de Akame ga Kill.',
                video_url='https://ok.ru/videoembed/14537217215214'
            )
            db.session.add(episode)
            db.session.commit()
            print("¡Episodio/Video añadido con éxito a Akame ga Kill!")
        else:
            # Si el episodio ya existe, actualizamos el link
            print("El episodio 1 ya existía, actualizando el link de video...")
            episode.video_url = 'https://ok.ru/videoembed/14537217215214'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
