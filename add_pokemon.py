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
        movie = Movie.query.filter(Movie.title.ilike('%Pokémon 3: El Hechizo de los Unown%')).first()
        
        if not movie:
            print("Creando la película 'Pokémon 3: El Hechizo de los Unown' en la base de datos...")
            movie = Movie(
                title='Pokémon 3: El Hechizo de los Unown',
                slug='pokemon-el-hechizo-de-los-unown',
                synopsis='Cuando el investigador Spencer Hale desaparece misteriosamente, los enigmáticos Unown responden a la tristeza de su hija Molly creando un mundo de ilusiones donde Entei se convierte en su padre. Ash, Pikachu y sus amigos deben entrar en esta extraña dimensión de cristal para salvar a Molly y a la madre de Ash, quien ha sido secuestrada por Entei.',
                year=2000,
                video_url='https://ok.ru/videoembed/10209981565678',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Pokémon 3 añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10209981565678'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
