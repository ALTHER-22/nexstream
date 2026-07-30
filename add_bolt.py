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
        movie = Movie.query.filter(Movie.title.ilike('%Baby Driver%')).first()
        
        if not movie:
            print("Creando la película 'Baby Driver' en la base de datos...")
            movie = Movie(
                title='Baby Driver (El Aprendiz del Crimen)',
                slug='baby-driver-el-aprendiz-del-crimen',
                synopsis='Baby es un joven y talentoso conductor especializado en fugas criminales que depende del ritmo de su música para ser el mejor al volante. Cuando conoce a la chica de sus sueños, ve la oportunidad de abandonar su vida delictiva. Pero tras ser forzado a trabajar para un jefe del crimen, deberá luchar por su vida y su libertad cuando un robo a mano armada sale mal.',
                year=2017,
                video_url='https://vkvideo.ru/video_ext.php?oid=200001672276&id=456239019&hash=65e0b2464980ff16&hd=4',
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
            print("¡Película Baby Driver añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://vkvideo.ru/video_ext.php?oid=200001672276&id=456239019&hash=65e0b2464980ff16&hd=4'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
