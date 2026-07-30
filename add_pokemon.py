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
        # Buscar o crear categoría Anime
        category = Category.query.filter_by(name='Anime').first()
        if not category:
            category = Category(name='Anime', slug='anime')
            db.session.add(category)
            db.session.commit()

        # Buscar si la película ya existe
        movie = Movie.query.filter(Movie.title.ilike('%Pokémon: Mewtwo vs Mew%')).first()
        
        if not movie:
            print("Creando la película 'Pokémon: Mewtwo vs Mew' en la base de datos...")
            movie = Movie(
                title='Pokémon: Mewtwo vs Mew',
                slug='pokemon-mewtwo-vs-mew',
                synopsis='Científicos crean a un poderoso clon de Mew llamado Mewtwo. Lleno de resentimiento, Mewtwo decide crear su propio ejército de clones para demostrar que son superiores a los originales y así vengarse de la humanidad. Ash, Pikachu y sus amigos deberán detenerlo en la batalla más épica antes de que destruya el mundo.',
                year=1998,
                video_url='https://ok.ru/videoembed/10209735346926',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Pokémon: Mewtwo vs Mew añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10209735346926'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
