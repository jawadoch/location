"""Génération PDF avec xhtml2pdf (100 % Python, compatible Windows sans dépendance système).

Pour afficher l'arabe, une police TrueType contenant les glyphes arabes est nécessaire.
On utilise en priorité une police déposée dans app/static/fonts (DocFont.ttf / DocFont-Bold.ttf),
sinon Arial ou Tahoma de Windows, sinon DejaVu Sans (Linux).
"""
import io
import os
from pathlib import Path

from flask import current_app, render_template, make_response
from xhtml2pdf import pisa
from xhtml2pdf.config.resources import ResourceAccessPolicy

from .logo import logo_path, logo_exists

FONT_CANDIDATES = [
    ("{static}/fonts/DocFont.ttf", "{static}/fonts/DocFont-Bold.ttf"),
    ("{windir}/Fonts/arial.ttf", "{windir}/Fonts/arialbd.ttf"),
    ("{windir}/Fonts/tahoma.ttf", "{windir}/Fonts/tahomabd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
]


def find_fonts():
    """Retourne (regular, bold) : chemins de police utilisables, ou (None, None)."""
    static = current_app.static_folder
    windir = os.environ.get("WINDIR", "C:/Windows")
    for regular, bold in FONT_CANDIDATES:
        regular = Path(regular.format(static=static, windir=windir))
        bold = Path(bold.format(static=static, windir=windir))
        if regular.is_file():
            return regular, (bold if bold.is_file() else regular)
    return None, None


def font_css(regular, bold):
    if not regular:
        return "body { font-family: Helvetica; }"
    return (
        "@font-face { font-family: DocFont; src: url('%s'); }\n"
        "@font-face { font-family: DocFont; src: url('%s'); font-weight: bold; }\n"
        "body { font-family: DocFont; }"
    ) % (regular.as_posix(), bold.as_posix())


def render_pdf(template, **context):
    """Rend un template HTML en PDF et retourne les octets."""
    regular, bold = find_fonts()
    context.setdefault("pdf_font_css", font_css(regular, bold))
    context.setdefault("pdf_arabic", regular is not None)
    logo = Path(logo_path()) if logo_exists() else None
    context.setdefault("logo_file", logo.as_posix() if logo else None)
    html = render_template(template, **context)

    roots = tuple({p.parent for p in (regular, bold, logo) if p})
    policy = ResourceAccessPolicy(base_dir=Path(current_app.static_folder), extra_roots=roots)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buffer, encoding="utf-8", resource_policy=policy)
    if result.err:
        raise RuntimeError("Erreur lors de la génération du PDF")
    return buffer.getvalue()


def pdf_response(template, filename, inline=False, **context):
    data = render_pdf(template, **context)
    response = make_response(data)
    response.headers["Content-Type"] = "application/pdf"
    disposition = "inline" if inline else "attachment"
    response.headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    return response
