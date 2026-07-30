import sys
try:
    from app import create_app
    from extensions import db
    from app.models.content import Movie, Category
except ImportError:
    print("Por favor, ejecuta desde la carpeta nexstream.")
    sys.exit(1)

app = create_app()

def run():
    with app.app_context():
        # Buscar o crear categoría Animación (o usar Anime/Infantil si prefieres)
        category = Category.query.filter_by(name='Animación').first()
        if not category:
            category = Category(name='Animación', slug='animacion')
            db.session.add(category)
            db.session.commit()

        # Buscar si la película ya existe
        movie = Movie.query.filter(Movie.title.ilike('%Reto Tokio%')).first()
        
        if not movie:
            print("Creando la película 'Rápido y Furioso: Reto Tokio' en la base de datos...")
            movie = Movie(
                title='Rápido y Furioso: Reto Tokio',
                slug='rapido-y-furioso-reto-tokio',
                synopsis='Sean Boswell es un joven rebelde que, para evitar ir a prisión por causar accidentes en carreras ilegales, es enviado a Tokio a vivir con su padre. Allí descubre el emocionante y peligroso mundo del "Drifting" (carreras de derrape). Tras perder un auto que no era suyo, Sean deberá aprender a derrapar para saldar su deuda y enfrentarse al temible "Rey del Drift", vinculado a la mafia japonesa yakuza.',
                year=2006,
                video_url='https://ok.ru/videoembed/12612207577782',
                is_active=True
            )
            # Categoría: Acción
            cat_accion = Category.query.filter_by(name='Acción').first()
            if not cat_accion:
                cat_accion = Category(name='Acción', slug='accion')
                db.session.add(cat_accion)
            movie.categories.append(cat_accion)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Rápido y Furioso: Reto Tokio añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/12612207577782'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
