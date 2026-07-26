"""
=============================================================================
NEXSTREAM — Punto de Entrada de la Aplicación
=============================================================================
Archivo: run.py
Descripción: Script principal para ejecutar el servidor de desarrollo Flask.
             En producción se usa Gunicorn, no este archivo.

Uso:
    Desarrollo:   python run.py  (o flask run)
    Producción:   gunicorn -c gunicorn.conf.py "run:application"
=============================================================================
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env antes de crear la app
load_dotenv()

from app import create_app

# Crear la aplicación con el entorno especificado
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Variable 'application' para compatibilidad con Gunicorn y WSGI servers
application = app

if __name__ == '__main__':
    """
    Solo se ejecuta en desarrollo local.
    En producción se usa: gunicorn run:application
    """
    app.run(
        host='0.0.0.0',     # Accesible desde la red local
        port=5000,
        debug=True,
        use_reloader=True,  # Auto-reload al cambiar código
        threaded=True,      # Múltiples peticiones simultáneas
    )
