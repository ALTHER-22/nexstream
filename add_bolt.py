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
        movie = Movie.query.filter(Movie.title.ilike('%Drive%')).first()
        
        if not movie:
            print("Creando la película 'Drive' en la base de datos...")
            movie = Movie(
                title='Drive',
                slug='drive-2011',
                synopsis='Un conductor misterioso trabaja como doble de acción en Hollywood durante el día y como conductor de huidas criminales por la noche. Su metódica vida da un giro violento cuando se enamora de su vecina Irene. Tras participar en un atraco que sale terriblemente mal para ayudar al esposo de ella recién salido de prisión, deberá usar todas sus habilidades al volante para proteger a las únicas personas que le importan.',
                year=2011,
                video_url='https://ok.ru/videoembed/12460053891766',
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
            print("¡Película Drive añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/12460053891766'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
