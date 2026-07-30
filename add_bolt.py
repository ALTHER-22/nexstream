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
        movie = Movie.query.filter(Movie.title.ilike('%Desperado%')).first()
        
        if not movie:
            print("Creando la película 'Desperado (La Balada del Pistolero)' en la base de datos...")
            movie = Movie(
                title='Desperado',
                slug='desperado-la-balada-del-pistolero',
                synopsis='El Mariachi se sumerge en el oscuro mundo del hampa en la frontera mexicana buscando venganza contra Bucho, el despiadado narcotraficante que mató a su amada. Armado con un estuche de guitarra lleno de armas, deja un rastro de sangre y balas a su paso mientras une fuerzas con Carolina, la hermosa dueña de una librería local que lo ayudará a enfrentarse al letal cartel.',
                year=1995,
                video_url='https://ok.ru/videoembed/3484283374220',
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
            print("¡Película Desperado añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/3484283374220'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
