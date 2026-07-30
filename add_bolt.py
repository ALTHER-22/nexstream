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
        movie = Movie.query.filter(Movie.title.ilike('%La Masacre de Texas: El Inicio%')).first()
        
        if not movie:
            print("Creando la película 'La Masacre de Texas: El Inicio' en la base de datos...")
            movie = Movie(
                title='La Masacre de Texas: El Inicio',
                slug='la-masacre-de-texas-el-inicio',
                synopsis='En 1969, dos hermanos y sus novias emprenden un viaje por carretera en Texas para pasar un último fin de semana juntos antes de ir a Vietnam. Tras un aparatoso accidente, caen en las garras de la sádica familia Hewitt. Este terrorífico viaje revelará los sangrientos orígenes de Thomas Hewitt, quien pronto se convertirá en el legendario y despiadado asesino conocido como Leatherface (Cara de Cuero).',
                year=2006,
                video_url='https://ok.ru/videoembed/11823008451283',
                is_active=True
            )
            # Categoría: Terror
            cat_terror = Category.query.filter_by(name='Terror').first()
            if not cat_terror:
                cat_terror = Category(name='Terror', slug='terror')
                db.session.add(cat_terror)
            movie.categories.append(cat_terror)
            db.session.add(movie)
            db.session.commit()
            print("¡Película La Masacre de Texas añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/11823008451283'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
