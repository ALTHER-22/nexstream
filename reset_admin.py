from app import create_app, db
from app.models.user import User, Role

app = create_app()

with app.app_context():
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("Error: No se encontró el rol de administrador en la base de datos.")
    else:
        # Buscar el primer usuario que tenga el rol de admin
        admin_user = User.query.filter(User.roles.contains(admin_role)).first()
        if not admin_user:
            print("Error: No se encontró ningún usuario administrador.")
        else:
            # Establecer nueva contraseña
            admin_user.set_password('Admin123!')
            db.session.commit()
            print("==================================================")
            print(f"¡Éxito! Se encontró el administrador:")
            print(f"Email: {admin_user.email}")
            print(f"Usuario: {admin_user.username}")
            print(f"NUEVA CONTRASEÑA: Admin123!")
            print("==================================================")
            print("Recuerda cambiarla desde tu perfil una vez que inicies sesión.")
