"""
=============================================================================
NEXSTREAM - Script de Inicializacion de la Base de Datos
=============================================================================
Archivo: init_db.py
Uso:
    python init_db.py          # Crear DB y datos iniciales
    python init_db.py --reset  # PELIGRO: borrar y recrear todo
=============================================================================
"""
# -*- coding: utf-8 -*-
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')  # Forzar UTF-8 en Windows

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from extensions import db
from app.models.user import User, Role
from app.models.content import Category, SiteConfig


def init_database(reset: bool = False):
    """Inicializar la base de datos con datos base."""

    app = create_app('development')

    with app.app_context():

        if reset:
            print("[!] Eliminando todas las tablas...")
            db.drop_all()
            print("[OK] Tablas eliminadas.")

        print("[...] Creando tablas...")
        db.create_all()
        print("[OK] Tablas creadas.")

        # Roles
        print("\n[...] Creando roles...")
        Role.insert_default_roles()
        print("[OK] Roles creados: admin, moderator, user")

        # Usuario Administrador
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@nexstream.com')
        existing_admin = User.query.filter_by(email=admin_email).first()

        if not existing_admin:
            print(f"\n[...] Creando usuario administrador: {admin_email}")
            admin = User(
                username='admin',
                email=admin_email,
                display_name='Administrador',
                is_verified=True,
                is_active=True,
            )
            admin.password = 'Admin1234!'
            admin.add_role('admin')
            db.session.add(admin)
            db.session.commit()
            print(f"[OK] Admin creado: {admin_email} / Admin1234!")
            print("[!!] RECUERDA CAMBIAR LA CONTRASENA DEL ADMIN")
        else:
            print(f"[--] El administrador {admin_email} ya existe.")

        # Categorias base
        print("\n[...] Creando categorias...")
        categories = [
            {'name': 'Accion',          'slug': 'accion',          'color': '#e50914', 'order': 1},
            {'name': 'Drama',           'slug': 'drama',           'color': '#6b48ff', 'order': 2},
            {'name': 'Comedia',         'slug': 'comedia',         'color': '#f5a623', 'order': 3},
            {'name': 'Terror',          'slug': 'terror',          'color': '#1a1a2e', 'order': 4},
            {'name': 'Ciencia Ficcion', 'slug': 'ciencia-ficcion', 'color': '#0ea5e9', 'order': 5},
            {'name': 'Anime',           'slug': 'anime',           'color': '#ec4899', 'order': 6},
            {'name': 'Documentales',    'slug': 'documentales',    'color': '#10b981', 'order': 7},
            {'name': 'Romance',         'slug': 'romance',         'color': '#f43f5e', 'order': 8},
            {'name': 'Thriller',        'slug': 'thriller',        'color': '#64748b', 'order': 9},
            {'name': 'Fantasia',        'slug': 'fantasia',        'color': '#8b5cf6', 'order': 10},
        ]

        for cat_data in categories:
            existing = Category.query.filter_by(slug=cat_data['slug']).first()
            if not existing:
                cat = Category(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    color=cat_data['color'],
                    order=cat_data['order'],
                    is_active=True,
                )
                db.session.add(cat)

        db.session.commit()
        print(f"[OK] {len(categories)} categorias creadas.")

        # Configuracion del sitio
        print("\n[...] Creando configuracion del sitio...")
        configs = [
            ('site_name',         'NEXSTREAM',                     'text',    'Nombre del sitio',        'general'),
            ('site_tagline',      'Tu universo de entretenimiento', 'text',    'Tagline del sitio',       'general'),
            ('items_per_page',    '24',                             'integer', 'Items por pagina',        'general'),
            ('registration_open', 'true',                           'boolean', 'Registro abierto',        'general'),
            ('maintenance_mode',  'false',                          'boolean', 'Modo mantenimiento',      'general'),
            ('hero_autoplay',     'true',                           'boolean', 'Hero autoplay',           'homepage'),
            ('show_trending',     'true',                           'boolean', 'Mostrar tendencias',      'homepage'),
            ('comments_enabled',  'true',                           'boolean', 'Comentarios habilitados', 'content'),
            ('ratings_enabled',   'true',                           'boolean', 'Valoraciones habilitadas','content'),
        ]

        for key, value, type_, label, group in configs:
            if not SiteConfig.query.filter_by(key=key).first():
                config_obj = SiteConfig(key=key, value=value, type=type_, label=label, group=group)
                db.session.add(config_obj)

        db.session.commit()
        print(f"[OK] {len(configs)} configuraciones creadas.")

        print("\n" + "="*60)
        print("NEXSTREAM - Base de datos lista y funcionando")
        print("="*60)
        print(f"  Admin:    {admin_email}")
        print( "  Password: Admin1234!  (<-- CAMBIALA EN PRODUCCION)")
        print( "  URL:      http://localhost:5000")
        print("="*60)


if __name__ == '__main__':
    reset = '--reset' in sys.argv
    if reset:
        confirm = input("⚠️  ¿Estás seguro de que quieres borrar toda la base de datos? (escribe 'SI'): ")
        if confirm != 'SI':
            print("Cancelado.")
            sys.exit(0)
    init_database(reset=reset)
