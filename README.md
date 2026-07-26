# 🎬 NEXSTREAM v2.0

> Plataforma de streaming premium construida con Flask + Python 3.14.
> Diseño inspirado en Netflix 2026 con identidad propia.

---

## ⚡ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.14, Flask 3.1, Blueprints |
| Base de Datos | SQLAlchemy 2.0, SQLite (dev) / PostgreSQL (prod) |
| Autenticación | Flask-Login, Flask-Bcrypt, itsdangerous |
| Formularios | Flask-WTF, WTForms |
| Seguridad | Flask-Limiter, Flask-Talisman, CSRF |
| Rendimiento | Flask-Caching, Flask-Compress |
| Frontend | HTML5, CSS3 moderno, JavaScript ES2026 |
| Diseño | Variables CSS, Glassmorphism, Dark/Light mode |

---

## 🚀 Inicio Rápido

### 1. Clonar y configurar

```bash
git clone <url>
cd nexstream
python -m venv venv
```

### 2. Activar entorno virtual

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

### 5. Inicializar base de datos

```bash
python init_db.py
```

### 6. Arrancar el servidor

```bash
python run.py
# → http://localhost:5000
```

---

## 📁 Estructura del Proyecto

```
nexstream/
├── app/
│   ├── __init__.py          # Application Factory
│   ├── auth/                # Blueprint: Autenticación
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── admin/               # Blueprint: Panel Admin
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/                # Blueprint: Páginas principales
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── api/                 # Blueprint: API REST
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py          # User, Role
│   │   ├── content.py       # Series, Movie, Season, Episode, Category
│   │   └── interaction.py   # Favorite, WatchHistory, Comment, Rating
│   ├── services/            # Lógica de negocio
│   ├── utils/               # Utilidades
│   ├── static/
│   │   ├── css/
│   │   │   ├── nexstream.css    # Design System
│   │   │   └── components.css  # Componentes UI
│   │   ├── js/
│   │   │   └── nexstream.js    # JavaScript principal
│   │   ├── images/
│   │   └── uploads/
│   └── templates/
│       ├── base.html            # Layout maestro
│       ├── components/          # Componentes reutilizables
│       ├── main/                # Templates del catálogo
│       ├── auth/                # Templates de autenticación
│       ├── admin/               # Templates del panel admin
│       └── errors/              # Páginas de error
├── config.py                # Configuración multi-entorno
├── extensions.py            # Extensiones Flask
├── run.py                   # Punto de entrada
├── init_db.py               # Inicializar DB
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔐 Credenciales por Defecto (Desarrollo)

| Campo | Valor |
|-------|-------|
| Email | admin@nexstream.com |
| Password | Admin1234! |

> ⚠️ **CAMBIAR EN PRODUCCIÓN**

---

## 🗺️ Módulos del Proyecto

| # | Módulo | Estado |
|---|--------|--------|
| 1 | **Fundación**: Config, DB, Design System | ✅ Completo |
| 2 | **Modelos completos + Migraciones** | ⏳ Próximo |
| 3 | **Autenticación completa** | ⏳ Pendiente |
| 4 | **CSS Avanzado + Animaciones** | ⏳ Pendiente |
| 5 | **Página Principal + Hero + Sliders** | ⏳ Pendiente |
| 6 | **Catálogo + Búsqueda + Filtros** | ⏳ Pendiente |
| 7 | **Reproductor de Video** | ⏳ Pendiente |
| 8 | **Panel Administrador** | ⏳ Pendiente |
| 9 | **Perfil de Usuario** | ⏳ Pendiente |
| 10 | **SEO + PWA + Optimización** | ⏳ Pendiente |

---

## 🌐 URLs de la Aplicación

| URL | Descripción |
|-----|-------------|
| `/` | Página principal |
| `/auth/login` | Iniciar sesión |
| `/auth/register` | Registro |
| `/admin/` | Panel de administración |
| `/api/v1/status` | Health check de la API |

---

## ⚙️ Comandos Útiles

```bash
# Inicializar/resetear DB
python init_db.py
python init_db.py --reset  # ¡PELIGRO! Borra todo

# Migraciones (cuando haya cambios en modelos)
flask db init
flask db migrate -m "Descripción del cambio"
flask db upgrade

# Shell interactivo (modelos disponibles sin importar)
flask shell

# Producción con Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:application
```

---

## 🔒 Seguridad

- ✅ Hash de contraseñas con bcrypt
- ✅ Protección CSRF en todos los formularios
- ✅ Rate limiting por IP
- ✅ Sesiones seguras (HttpOnly, SameSite)
- ✅ Protección XSS (Jinja2 auto-escaping)
- ✅ Bloqueo de cuenta tras 5 intentos fallidos
- ✅ Tokens seguros para recuperación de contraseña

---

*Desarrollado con ❤️ — NEXSTREAM v2.0.0 © 2026*
