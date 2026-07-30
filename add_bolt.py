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
        movie = Movie.query.filter(Movie.title.ilike('%Bolt%')).first()
        
        if not movie:
            print("Creando la película 'Bolt: Un perro fuera de serie' en la base de datos...")
            movie = Movie(
                title='Bolt: Un perro fuera de serie',
                slug='bolt-un-perro-fuera-de-serie',
                synopsis='Para el superperro Bolt, todos los días están llenos de aventuras, peligro e intriga... al menos hasta que las cámaras dejan de grabar, ya que es el protagonista de un famoso programa de televisión. Cuando es enviado por accidente desde sus estudios de Hollywood a Nueva York, comienza su mayor aventura en el mundo real, donde descubrirá junto a un gato callejero y un hámster que no necesita superpoderes para ser un héroe.',
                year=2008,
                video_url='https://ok.ru/videoembed/9952445401838',
                is_active=True
            )
            movie.categories.append(category)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Bolt añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/9952445401838'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
