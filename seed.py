import os
from datetime import datetime, timezone
from app import create_app
from extensions import db
from app.models import User, Category, Series, Movie, Season, Episode, Banner

app = create_app('development')

def seed_database():
    with app.app_context():
        # Limpiar datos anteriores (opcional, cuidado en prod)
        db.drop_all()
        db.create_all()

        # Insertar roles por defecto
        from app.models.user import Role
        Role.insert_default_roles()

        print("Creando usuario administrador...")
        admin = User(
            username='admin',
            email='admin@bacanus.com',
            is_active=True,
            is_verified=True
        )
        admin.password = 'admin123'
        
        # Asignar rol de admin
        admin_role = Role.query.filter_by(name='admin').first()
        admin.roles.append(admin_role)
        
        db.session.add(admin)

        print("Creando categorías...")
        cats = [
            Category(name='Acción', slug='accion', icon='🔥'),
            Category(name='Ciencia Ficción', slug='sci-fi', icon='🚀'),
            Category(name='Drama', slug='drama', icon='🎭'),
            Category(name='Comedia', slug='comedia', icon='😂'),
            Category(name='Documentales', slug='documentales', icon='🌍')
        ]
        db.session.add_all(cats)
        db.session.commit()

        print("Creando series...")
        s1 = Series(
            title='Cyberpunk 2077: Edgerunners',
            slug='cyberpunk-edgerunners',
            synopsis='En una distopía plagada de corrupción y ciberimplantes, un joven talento y temerario de las calles aspira a ser un edgerunner.',
            year=2022,
            is_active=True,
            is_featured=True,
            cover='cyberpunk-cover.webp',
            banner='cyberpunk-banner.webp',
            rating_avg=9.5,
            rating_count=150
        )
        s1.categories.append(cats[0])
        s1.categories.append(cats[1])
        db.session.add(s1)
        db.session.commit()

        season1 = Season(series_id=s1.id, number=1, title='Temporada 1')
        db.session.add(season1)
        db.session.commit()

        for i in range(1, 4):
            ep = Episode(
                season_id=season1.id,
                number=i,
                title=f'Episodio {i}',
                description=f'Sinopsis increíble del episodio {i}.',
                duration=1500,
                is_active=True,
                video_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4'
            )
            db.session.add(ep)

        print("Creando películas...")
        m1 = Movie(
            title='Blade Runner 2049',
            slug='blade-runner-2049',
            synopsis='Un nuevo blade runner descubre un secreto largamente oculto que podría acabar con el caos que impera en la sociedad.',
            year=2017,
            duration=164,
            is_active=True,
            is_featured=True,
            cover='bladerunner-cover.webp',
            banner='bladerunner-banner.webp',
            rating_avg=9.8,
            rating_count=320,
            video_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4'
        )
        m1.categories.append(cats[1])
        db.session.add(m1)

        print("Creando banners promocionales...")
        b1 = Banner(
            title='Cyberpunk 2077: Edgerunners',
            subtitle='¡NUEVA SERIE EXCLUSIVA!',
            description='Sumérgete en Night City.',
            link_url='/serie/cyberpunk-edgerunners',
            image_desktop='cyberpunk-banner.webp',
            image_mobile='cyberpunk-cover.webp',
            position=1,
            is_active=True
        )
        b2 = Banner(
            title='Blade Runner 2049',
            subtitle='CLÁSICO DE CIENCIA FICCIÓN',
            description='La obra maestra de Denis Villeneuve ya está disponible en 4K.',
            link_url='/pelicula/blade-runner-2049',
            image_desktop='bladerunner-banner.webp',
            image_mobile='bladerunner-cover.webp',
            position=2,
            is_active=True
        )
        db.session.add_all([b1, b2])

        db.session.commit()
        print("¡Base de datos sembrada con éxito!")

if __name__ == '__main__':
    seed_database()
