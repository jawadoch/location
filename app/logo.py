"""Logo de l'agence, recadré et fond blanchi pour l'impression.

- Logo par défaut livré avec l'application : static/img/logo.png
- Logo envoyé depuis Paramètres : instance/logo.png (données du client, conservé lors des mises à jour)
- instance/logo.off : logo désactivé (le nom de l'agence est affiché à la place)
"""
import os

from flask import current_app, url_for
from PIL import Image, ImageOps


def _default_path():
    return os.path.join(current_app.static_folder, "img", "logo.png")


def _upload_path():
    return os.path.join(current_app.instance_path, "logo.png")


def _disabled_flag():
    return os.path.join(current_app.instance_path, "logo.off")


def logo_path():
    """Chemin du logo à utiliser, ou None si aucun logo."""
    if os.path.isfile(_disabled_flag()):
        return None
    for path in (_upload_path(), _default_path()):
        if os.path.isfile(path):
            return path
    return None


def logo_exists():
    return logo_path() is not None


def logo_url():
    """URL du logo avec un paramètre de version pour éviter le cache du navigateur."""
    path = logo_path()
    if path is None:
        return None
    return url_for("main.logo", v=int(os.path.getmtime(path)))


def remove_logo():
    if os.path.isfile(_upload_path()):
        os.remove(_upload_path())
    open(_disabled_flag(), "w").close()


def save_logo(source, dest=None):
    """Recadre l'image sur son contenu, blanchit le fond clair et l'enregistre en PNG."""
    dest = dest or _upload_path()
    image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    gray = image.convert("L")
    # Le fond (papier légèrement gris) devient blanc pur
    mask = gray.point(lambda p: 255 if p < 190 else 0)
    bbox = mask.getbbox()
    if bbox:
        pad = max(8, int(min(image.size) * 0.02))
        left, top, right, bottom = bbox
        image = image.crop((
            max(0, left - pad), max(0, top - pad),
            min(image.width, right + pad), min(image.height, bottom + pad),
        ))
        gray = image.convert("L")
    white = Image.new("RGB", image.size, (255, 255, 255))
    image = Image.composite(image, white, gray.point(lambda p: 255 if p < 215 else 0))
    if image.width > 1200:
        image = image.resize((1200, round(image.height * 1200 / image.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    image.save(dest, "PNG", optimize=True)
    if dest == _upload_path() and os.path.isfile(_disabled_flag()):
        os.remove(_disabled_flag())
    return dest
