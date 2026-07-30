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
        movie = Movie.query.filter(Movie.title.ilike('%Pokémon 5: Latios y Latias%')).first()
        
        if not movie:
            print("Creando la película 'Pokémon 5: Latios y Latias' en la base de datos...")
            movie = Movie(
                title='Pokémon 5: Latios y Latias',
                slug='pokemon-latios-y-latias',
                synopsis='Ash, Pikachu y sus amigos llegan a Altomare, la hermosa capital del agua. Allí conocen a Latios y Latias, dos misteriosos Pokémon legendarios que protegen la ciudad y la Joya del Alma. Cuando un par de famosas ladronas intentan robar la joya, desencadenan una catástrofe que amenaza con hundir la ciudad entera.',
                year=2002,
                video_url='https://ok.ru/videoembed/10214016944878',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Pokémon 5 añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10214016944878'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
