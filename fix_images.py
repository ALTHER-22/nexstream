import os
import urllib.request
import sys
import ssl

try:
    from app import create_app
    from extensions import db
    from app.models.content import Series
except ImportError:
    print("Por favor, ejecuta desde la carpeta nexstream.")
    sys.exit(1)

app = create_app()

def download_image(url, filename, folder):
    filepath = os.path.join(app.root_path, 'static', 'uploads', folder, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as response, open(filepath, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        return f"uploads/{folder}/{filename}"
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return None

def run():
    with app.app_context():
        series = Series.query.filter_by(slug='kenichi-el-discipulo-mas-fuerte').first()
        if not series:
            print("Serie no encontrada.")
            return

        print("Descargando poster...")
        # URL oficial de MyAnimeList
        poster_url = "https://cdn.myanimelist.net/images/anime/8/75507l.jpg"
        cover_path = download_image(poster_url, "kenichi_cover.jpg", "covers")
        
        print("Descargando banner...")
        # Imagen de fondo general
        banner_url = "https://images.alphacoders.com/264/thumb-1920-264627.jpg"
        banner_path = download_image(banner_url, "kenichi_banner.jpg", "banners")

        if cover_path:
            series.cover = cover_path
            print("Poster actualizado!")
        if banner_path:
            series.banner = banner_path
            print("Banner actualizado!")
            
        db.session.commit()
        print("¡Todo listo! Las imágenes están guardadas en tu servidor.")

if __name__ == '__main__':
    run()
