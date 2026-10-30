"""Fonctions utilitaires : conversion des champs de formulaire, numérotation, modèles."""
import math
import re
from datetime import datetime, date

from sqlalchemy import func

from .extensions import db


# ---------------------------------------------------------------- formulaires

def form_str(form, key, default=""):
    return (form.get(key) or default).strip()


def form_date(form, key):
    value = (form.get(key) or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def form_datetime(form, key):
    value = (form.get(key) or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def form_float(form, key, default=0.0):
    value = (form.get(key) or "").strip().replace(" ", "").replace(",", ".")
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def form_int(form, key, default=None):
    value = (form.get(key) or "").strip().replace(" ", "")
    if not value:
        return default
    try:
        return int(float(value.replace(",", ".")))
    except ValueError:
        return default


def form_bool(form, key):
    return form.get(key) in ("1", "on", "true", "oui")


_ARABIC_RE = re.compile(r"[؀-ۿ]")


def is_arabic(text):
    """Vrai si le texte contient majoritairement de l'arabe (document à afficher de droite à gauche)."""
    text = text or ""
    arabic = len(_ARABIC_RE.findall(text))
    latin = len(re.findall(r"[A-Za-zÀ-ÿ]", _PLACEHOLDER_RE.sub("", text)))
    return arabic > 0 and arabic >= latin


def rental_days(start, end):
    """Nombre de jours facturés : toute période de 24 h entamée compte (minimum 1)."""
    if not start or not end or end <= start:
        return 1
    return max(1, math.ceil((end - start).total_seconds() / 86400))


# ---------------------------------------------------------------- numérotation

def next_number(model, prefix, year=None):
    """Retourne le prochain numéro libre au format PREFIX-AAAA-0001."""
    year = year or date.today().year
    base = f"{prefix}-{year}-"
    numbers = db.session.query(model.number).filter(model.number.like(base + "%")).all()
    highest = 0
    for (num,) in numbers:
        tail = num[len(base):]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return f"{base}{highest + 1:04d}"


# ---------------------------------------------------------------- recherche

def search_filter(columns, query):
    """Construit un filtre OR insensible à la casse sur plusieurs colonnes."""
    from sqlalchemy import or_

    q = f"%{query.strip().lower()}%"
    return or_(*[func.lower(col).like(q) for col in columns])


# ---------------------------------------------------------------- modèles d'engagement

PLACEHOLDERS = {
    "client_nom": "Nom et prénom du client",
    "client_cin": "N° CIN",
    "client_passeport": "N° passeport",
    "client_permis": "N° permis de conduire",
    "client_adresse": "Adresse du client",
    "client_telephone": "Téléphone du client",
    "client_nationalite": "Nationalité",
    "vehicule": "Marque et modèle du véhicule",
    "immatriculation": "Immatriculation",
    "contrat_numero": "N° du contrat lié",
    "montant": "Montant",
    "date_debut": "Date de début",
    "date_fin": "Date de fin",
    "date": "Date du document",
    "lieu": "Lieu",
    "agence_nom": "Nom de l'agence",
    "agence_adresse": "Adresse de l'agence",
    "agence_ville": "Ville de l'agence",
    "agence_telephone": "Téléphone de l'agence",
}

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def fmt_date(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return value.strftime("%d/%m/%Y")


def fmt_money(value, currency="DH"):
    if value is None:
        return ""
    text = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{text} {currency}".strip()


NATIONALITIES_AR = {
    "marocaine": "مغربية", "marocain": "مغربي", "française": "فرنسية", "français": "فرنسي",
    "espagnole": "إسبانية", "espagnol": "إسباني", "algérienne": "جزائرية", "algérien": "جزائري",
    "tunisienne": "تونسية", "tunisien": "تونسي", "mauritanienne": "موريتانية", "mauritanien": "موريتاني",
    "sénégalaise": "سنغالية", "sénégalais": "سنغالي", "belge": "بلجيكية", "italienne": "إيطالية",
    "italien": "إيطالي", "allemande": "ألمانية", "allemand": "ألماني", "britannique": "بريطانية",
    "américaine": "أمريكية", "américain": "أمريكي", "néerlandaise": "هولندية", "néerlandais": "هولندي",
}

CURRENCIES_AR = {"DH": "درهم", "MAD": "درهم", "DHS": "درهم"}


def ltr_isolate(value):
    """Encadre une valeur latine/numérique (ex. 12345-A-6) de marques LRM (U+200E, invisibles et
    présentes dans Arial) pour qu'elle garde son ordre de lecture dans un texte arabe."""
    if value and re.search(r"[A-Za-z0-9]", value) and not _ARABIC_RE.search(value):
        return "‎" + value + "‎"
    return value


def engagement_context(engagement, agency):
    arabic = is_arabic(engagement.body_source)
    nationality = engagement.client_nationality or ""
    currency = agency.currency or ""
    if arabic:
        nationality = NATIONALITIES_AR.get(nationality.strip().lower(), nationality)
        currency = CURRENCIES_AR.get(currency.strip().upper(), currency)
    context = _engagement_values(engagement, agency, nationality, currency)
    if arabic:
        context = {k: ltr_isolate(v) for k, v in context.items()}
        if engagement.amount:
            context["montant"] = f"{ltr_isolate(fmt_money(engagement.amount, ''))} {currency}"
    return context


def _engagement_values(engagement, agency, nationality, currency):
    return {
        "client_nom": engagement.client_name or "",
        "client_cin": engagement.client_cin or "",
        "client_passeport": engagement.client_passport or "",
        "client_permis": engagement.client_license_no or "",
        "client_adresse": engagement.client_address or "",
        "client_telephone": engagement.client_phone or "",
        "client_nationalite": nationality,
        "vehicule": engagement.vehicle_label or "",
        "immatriculation": engagement.vehicle_plate or "",
        "contrat_numero": engagement.contract_number or "",
        "montant": fmt_money(engagement.amount, currency) if engagement.amount else "",
        "date_debut": fmt_date(engagement.start_date),
        "date_fin": fmt_date(engagement.end_date),
        "date": fmt_date(engagement.doc_date),
        "lieu": engagement.place or agency.city or "",
        "agence_nom": agency.name or "",
        "agence_adresse": agency.address or "",
        "agence_ville": agency.city or "",
        "agence_telephone": agency.phone or "",
    }


def render_placeholders(text, context):
    """Remplace les variables {{ nom }} connues ; les inconnues restent intactes."""

    def repl(match):
        key = match.group(1)
        if key in context:
            return str(context[key]) if context[key] != "" else "........................"
        return match.group(0)

    return _PLACEHOLDER_RE.sub(repl, text or "")
