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
        category = Category.query.filter_by(name='Animación').first()
        if not category:
            category = Category(name='Animación', slug='animacion')
            db.session.add(category)
            db.session.commit()

        movie = Movie.query.filter_by(title='Rio').first()
        if not movie:
            print("Añadiendo Rio a la base de datos...")
            movie = Movie(
                title='Rio',
                slug='rio',
                synopsis='Cuando Blu, un guacamayo domesticado de un pequeño pueblo de Minnesota, conoce a la ferozmente independiente Perla, emprende una aventura en Río de Janeiro junto a la guacamaya de sus sueños.',
                year=2011,
                video_url='https://ok.ru/video/11101527935726',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Rio añadida con éxito!")
        else:
            print("La película ya existía.")

if __name__ == '__main__':
    run()
