import sqlite3
import os
import bcrypt

db_path = os.path.join(os.getcwd(), 'instance', 'nexstream.db')

if not os.path.exists(db_path):
    print("ERROR: No se encuentra la base de datos en", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Desbloqueando a todos los usuarios...")
cursor.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL")
conn.commit()

# Hash 'Admin123!'
password_hash = bcrypt.hashpw('Admin123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("Actualizando contraseña de admin@bacanus.com...")
cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (password_hash, 'admin@bacanus.com'))
if cursor.rowcount > 0:
    print("Contraseña actualizada con éxito.")
else:
    print("No se encontró el usuario admin@bacanus.com en la base de datos.")

conn.commit()
conn.close()

print("PROCESO TERMINADO. Intenta iniciar sesión.")
