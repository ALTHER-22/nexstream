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
        movie = Movie.query.filter(Movie.title.ilike('%Amos del universo%')).first()
        
        if not movie:
            print("Creando la película 'Amos del universo' en la base de datos...")
            movie = Movie(
                title='Amos del universo',
                slug='amos-del-universo-2026',
                synopsis='En esta espectacular película, el príncipe Adam descubre su destino como el protector de Eternia. Al empuñar la Espada del Poder y transformarse en He-Man, deberá enfrentarse al despiadado Skeletor y sus fuerzas oscuras, quienes planean apoderarse del místico Castillo Grayskull para desatar su poder maligno sobre todo el universo.',
                year=2026,
                video_url='https://ok.ru/videoembed/14769364798190',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Amos del universo añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/14769364798190'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
