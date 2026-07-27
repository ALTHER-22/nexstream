from dotenv import load_dotenv
import os
import smtplib
from email.message import EmailMessage

# Cargar las variables de entorno desde .env
load_dotenv('.env')

username = os.environ.get('MAIL_USERNAME')
password = os.environ.get('MAIL_PASSWORD')

print(f"Probando conexión SMTP con el correo: {username}")

if not username or not password:
    print("ERROR: MAIL_USERNAME o MAIL_PASSWORD están vacíos en el archivo .env")
    exit(1)

msg = EmailMessage()
msg.set_content("Este es un correo de prueba de NEXSTREAM para verificar que el SMTP funciona.")
msg['Subject'] = 'Prueba SMTP NEXSTREAM'
msg['From'] = username
msg['To'] = username

try:
    print("Conectando a smtp.gmail.com:587...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(1)  # Mostrar todo el log de conexión
    server.starttls()
    
    print("Intentando iniciar sesión...")
    server.login(username, password)
    
    print("Inició sesión con éxito. Enviando correo...")
    server.send_message(msg)
    
    server.quit()
    print("==========================================")
    print("¡EL CORREO SE ENVIÓ CON ÉXITO! Revisa tu bandeja de entrada.")
    print("==========================================")

except smtplib.SMTPAuthenticationError as e:
    print("==========================================")
    print("ERROR DE AUTENTICACIÓN (Contraseña incorrecta o bloqueada por Google)")
    print(f"Detalle: {e}")
    print("==========================================")
except Exception as e:
    print("==========================================")
    print("OCURRIÓ UN ERROR INESPERADO:")
    print(f"Detalle: {e}")
    print("==========================================")
