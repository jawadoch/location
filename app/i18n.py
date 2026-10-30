"""Interface bilingue arabe / français.

Les textes sont écrits en français dans le code et les templates via _("...") ;
en arabe, ils sont remplacés par leur traduction (app/translations_ar.py).
La langue choisie est mémorisée dans un cookie ; par défaut : DEFAULT_LANGUAGE (arabe).
"""
from flask import current_app, has_request_context, request

from .translations_ar import AR

LANGUAGES = {"ar": "عربي", "fr": "Français"}
COOKIE = "lang"


def get_lang():
    if has_request_context():
        lang = request.cookies.get(COOKIE)
        if lang in LANGUAGES:
            return lang
    return current_app.config.get("DEFAULT_LANGUAGE", "ar")


def is_rtl():
    return get_lang() == "ar"


def _(text, **values):
    """Traduit un texte français dans la langue de l'interface (avec variables {nom})."""
    if get_lang() == "ar":
        text = AR.get(text, text)
    return text.format(**values) if values else text


# Textes utilisés par app.js
JS_TEXTS = [
    "Client existant :",
    "Délier",
    "Aucun client trouvé — saisissez ses informations ci-dessous, la fiche sera créée automatiquement.",
    "CIN",
    "Passeport",
    "Tél",
    "Remplacer le texte actuel par celui du modèle ?",
]


def js_texts():
    return {text: _(text) for text in JS_TEXTS}
