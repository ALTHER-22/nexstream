import sys
from app import create_app, db
from app.models.user import User, Role

app = create_app()

with app.app_context():
    print("Verificando roles...")
    Role.insert_default_roles()
    
    admin_role = Role.query.filter_by(name='admin').first()
    
    admin_user = User.query.filter(User.roles.contains(admin_role)).first()
    
    if not admin_user:
        print("No se encontró un administrador. Creando uno nuevo...")
        admin_user = User(
            username='admin',
            email='admin@nexstream.com',
            display_name='Administrador',
            is_verified=True
        )
        admin_user.set_password('Admin123!')
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        db.session.commit()
        print("==================================================")
        print(f"¡Éxito! Administrador CREADO:")
        print(f"Email: admin@nexstream.com")
        print(f"Usuario: admin")
        print(f"Contraseña: Admin123!")
        print("==================================================")
    else:
        admin_user.set_password('Admin123!')
        admin_user.failed_login_attempts = 0
        admin_user.locked_until = None
        db.session.commit()
        print("==================================================")
        print(f"¡Éxito! Se encontró el administrador:")
        print(f"Email: {admin_user.email}")
        print(f"Usuario: {admin_user.username}")
        print(f"NUEVA CONTRASEÑA: Admin123!")
        print("==================================================")
