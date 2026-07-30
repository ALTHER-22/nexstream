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
        movie = Movie.query.filter(Movie.title.ilike('%Ratatouille%')).first()
        
        if not movie:
            print("Creando la película 'Ratatouille' en la base de datos...")
            movie = Movie(
                title='Ratatouille',
                slug='ratatouille',
                synopsis='Remy es una simpática rata que sueña con convertirse en un gran chef francés a pesar de la oposición de su familia. Cuando el destino lleva a Remy a París, descubre que está situado justo debajo del restaurante de su ídolo culinario, Auguste Gusteau. A pesar del peligro evidente de ser un roedor en la cocina de un restaurante, su pasión lo unirá a un joven y despistado lavaplatos llamado Linguini para crear la combinación perfecta.',
                year=2007,
                video_url='https://ok.ru/videoembed/9823113448174',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Ratatouille añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/9823113448174'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
