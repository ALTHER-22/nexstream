import urllib.request
import json
import ssl
import sys
import os

# Importar la app de Flask y la base de datos
try:
    from app import create_app
    from extensions import db
    from app.models.content import Series, Season, Episode, Category
except ImportError:
    print("Por favor, ejecuta este script desde el directorio raíz de nexstream.")
    sys.exit(1)

app = create_app()

def run():
    with app.app_context():
        # 1. Obtener la categoría Anime
        category = Category.query.filter_by(name='Anime').first()
        if not category:
            category = Category(name='Anime', slug='anime')
            db.session.add(category)
            db.session.commit()

        # 2. Buscar si ya existe la serie
        series = Series.query.filter_by(title='Kenichi: El discípulo más fuerte').first()
        if series:
            print("La serie 'Kenichi' ya existe en la base de datos.")
        else:
            # Info manual
            print("Configurando información de Kenichi...")
            synopsis = 'Kenichi Shirahama es un estudiante de preparatoria débil y tímido del que todos abusan. Tras conocer a la misteriosa Miu Fūrinji, Kenichi decide unirse al dojo Ryozanpaku, donde habitan los maestros de artes marciales más fuertes del mundo.'
            poster = 'https://image.tmdb.org/t/p/w500/yZc5yW9w3O5i4O9w0S9P3X0V5v1.jpg' 
            banner_img = 'https://image.tmdb.org/t/p/original/iY6R9O2NlJk3U1l0Z0M2o7P5A5d.jpg'

            print("Creando la serie en la base de datos...")
            series = Series(
                title='Kenichi: El discípulo más fuerte',
                original_title='Shijou Saikyou no Deshi Kenichi',
                slug='kenichi-el-discipulo-mas-fuerte',
                synopsis=synopsis,
                year=2006,
                status='COMPLETED',
                is_active=True,
                banner=banner_img,
                cover=poster,
            )
            series.categories.append(category)
            db.session.add(series)
            db.session.commit()

        # 3. Crear Temporada 1
        season = Season.query.filter_by(series_id=series.id, number=1).first()
        if not season:
            season = Season(series_id=series.id, number=1, title='Temporada 1')
            db.session.add(season)
            db.session.commit()
            
        # 4. Crear Episodio (La animación completa de 50 capítulos)
        episode = Episode.query.filter_by(season_id=season.id, number=1).first()
        if not episode:
            print("Añadiendo el video...")
            episode = Episode(
                season_id=season.id,
                number=1,
                title='La Serie Completa (Cap 1-50)',
                description='Recopilación de los 50 capítulos de Kenichi: El discípulo más fuerte en un solo video.',
                video_url='https://ok.ru/videoembed/14328363027182'
            )
            db.session.add(episode)
            db.session.commit()
            print("¡Serie Kenichi añadida con éxito a tu plataforma!")
        else:
            print("El episodio ya estaba añadido.")

if __name__ == '__main__':
    run()
