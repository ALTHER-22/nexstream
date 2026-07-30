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
        movie = Movie.query.filter(Movie.title.ilike('%Pokémon 2: El poder de Uno%')).first()
        
        if not movie:
            print("Creando la película 'Pokémon 2: El poder de Uno' en la base de datos...")
            movie = Movie(
                title='Pokémon 2: El poder de Uno',
                slug='pokemon-el-poder-de-uno',
                synopsis='Ash y sus amigos llegan a la Isla Shamouti, donde la leyenda cuenta que un Elegido debe reunir los tres tesoros para evitar la destrucción del mundo si los legendarios Articuno, Zapdos y Moltres son perturbados por un misterioso coleccionista.',
                year=1999,
                video_url='https://ok.ru/videoembed/10207933893358',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Pokémon 2: El poder de Uno añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10207933893358'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
