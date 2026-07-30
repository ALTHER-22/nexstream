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
        movie = Movie.query.filter(Movie.title.ilike('%Pokémon 4: Celebi, la Voz del Bosque%')).first()
        
        if not movie:
            print("Creando la película 'Pokémon 4: Celebi, la Voz del Bosque' en la base de datos...")
            movie = Movie(
                title='Pokémon 4: Celebi, la Voz del Bosque',
                slug='pokemon-celebi-la-voz-del-bosque',
                synopsis='Ash y Pikachu viajan a un misterioso bosque habitado por Celebi, el mítico Pokémon que puede viajar en el tiempo. Allí se encuentran con Sammy, un chico que ha sido transportado 40 años desde el pasado para proteger a Celebi de un malvado cazador del Team Rocket, que planea usar el poder del tiempo para sus oscuros propósitos.',
                year=2001,
                video_url='https://ok.ru/videoembed/10213846485742',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Pokémon 4 añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10213846485742'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
