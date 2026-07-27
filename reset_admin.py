import sys
from app import create_app, db
from app.models.user import User, Role

app = create_app()

with app.app_context():
    print("Verificando roles...")
    Role.insert_default_roles()
    admin_role = Role.query.filter_by(name='admin').first()
    
    # Unlock EVERYONE just in case
    all_users = User.query.all()
    for u in all_users:
        u.failed_login_attempts = 0
        u.locked_until = None
    
    # Try to find bacanus or admin@bacanus.com
    target_user = User.query.filter((User.email == 'admin@bacanus.com') | (User.username == 'bacanus') | (User.username == 'admin')).first()
    
    if not target_user:
        target_user = User.query.filter(User.roles.contains(admin_role)).first()
        
    if not target_user:
        print("No se encontró usuario. Creando uno nuevo...")
        target_user = User(
            username='admin',
            email='admin@bacanus.com',
            display_name='Administrador',
            is_verified=True
        )
        db.session.add(target_user)
        
    target_user.set_password('Admin123!')
    if admin_role not in target_user.roles:
        target_user.roles.append(admin_role)
        
    target_user.failed_login_attempts = 0
    target_user.locked_until = None
    
    db.session.commit()
    print("==================================================")
    print(f"¡Éxito! Cuenta de administrador lista:")
    print(f"Email: {target_user.email}")
    print(f"Usuario: {target_user.username}")
    print(f"NUEVA CONTRASEÑA: Admin123!")
    print("==================================================")
