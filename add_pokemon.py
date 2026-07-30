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
        movie = Movie.query.filter(Movie.title.ilike('%Pokémon 6: Jirachi y los Deseos%')).first()
        
        if not movie:
            print("Creando la película 'Pokémon 6: Jirachi y los Deseos' en la base de datos...")
            movie = Movie(
                title='Pokémon 6: Jirachi y los Deseos',
                slug='pokemon-jirachi-y-los-deseos',
                synopsis='Ash, Pikachu y sus amigos visitan un increíble festival itinerante por la llegada del Cometa Milenario. Allí descubren a Jirachi, un tierno y mítico Pokémon que despierta solo cada mil años para conceder deseos. Sin embargo, un malvado mago planea usar el poder de Jirachi para despertar a un ser destructivo. Ash deberá arriesgar todo para salvar a su nuevo amigo.',
                year=2003,
                video_url='https://ok.ru/videoembed/10213891443438',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Pokémon 6 añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10213891443438'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
