try:
    from app import create_app
    from extensions import db
    from app.models.content import Movie
except ImportError:
    import sys
    print("Por favor, ejecuta desde la carpeta nexstream.")
    sys.exit(1)

app = create_app()

def run():
    with app.app_context():
        # Buscar la película de Akame ga Kill
        movie = Movie.query.filter(Movie.title.ilike('%Akame ga Kill%')).first()
        
        if not movie:
            print("No se encontró 'Akame ga Kill' en la base de datos (se buscó como Película).")
            print("Por favor créala primero en el Panel de Administración -> Películas.")
            return

        print("Añadiendo el video a Akame ga Kill...")
        movie.video_url = 'https://ok.ru/videoembed/14537217215214'
        db.session.commit()
        print("¡Video añadido con éxito a Akame ga Kill!")

if __name__ == '__main__':
    run()
