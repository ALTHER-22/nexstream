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
        movie = Movie.query.filter(Movie.title.ilike('%Estación Zombie%')).first()
        
        if not movie:
            print("Creando la película 'Estación Zombie' en la base de datos...")
            movie = Movie(
                title='Estación Zombie',
                slug='estacion-zombie-tren-a-busan',
                synopsis='Un brote viral misterioso pone a Corea en estado de emergencia. Sok-woo y su hija Soo-ahn suben al tren bala KTX de Seúl a Busan, el único refugio seguro. Sin embargo, justo antes de partir, la estación es invadida por personas infectadas que rápidamente se transforman en violentos zombis sedientos de sangre, dando inicio a un terrorífico viaje de supervivencia en un espacio cerrado.',
                year=2016,
                video_url='https://ok.ru/videoembed/10452727565011',
                is_active=True
            )
            # NOTA: Estación zombie no es animación, así que deberíamos usar otra categoría, 
            # pero por ahora la dejaremos en la categoría actual o crearemos una de Terror/Acción si no se asigna.
            # Para evitar errores, le asignaremos la primera categoría que encuentre o 'Acción'
            cat_accion = Category.query.filter_by(name='Acción').first()
            if not cat_accion:
                cat_accion = Category(name='Acción', slug='accion')
                db.session.add(cat_accion)
            movie.categories.append(cat_accion)
            db.session.add(movie)
            db.session.commit()
            print("¡Película Estación Zombie añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/10452727565011'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
