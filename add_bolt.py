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
        movie = Movie.query.filter(Movie.title.ilike('%El Demonio%')).first()
        
        if not movie:
            print("Creando la película 'El Demonio' en la base de datos...")
            movie = Movie(
                title='El Demonio (Jeepers Creepers)',
                slug='el-demonio-jeepers-creepers',
                synopsis='Los hermanos Trish y Darry viajan por una carretera desolada para pasar las vacaciones en casa. Su viaje se convierte en una pesadilla cuando descubren el espeluznante secreto que oculta un misterioso conductor en el sótano de una iglesia abandonada. Pronto se ven perseguidos por el "Creeper", un terrorífico ser sobrenatural que despierta cada 23 años durante 23 días para alimentarse de partes humanas.',
                year=2001,
                video_url='https://ok.ru/videoembed/3341535152675',
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
            print("¡Película El Demonio añadida con éxito!")
        else:
            print("La película ya existía, actualizando el link de video...")
            movie.video_url = 'https://ok.ru/videoembed/3341535152675'
            db.session.commit()
            print("¡Video actualizado con éxito!")

if __name__ == '__main__':
    run()
