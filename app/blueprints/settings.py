import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from PIL import Image

from ..extensions import db
from ..logo import save_logo, logo_exists, remove_logo
from ..models import Agency
from ..utils import form_str, form_float

bp = Blueprint("settings", __name__)

TEXT_FIELDS = [
    "name", "name_ar", "slogan", "address", "city", "phone", "email", "website",
    "ice", "rc", "tax_id", "patente", "currency",
]


@bp.route("/", methods=["GET", "POST"])
def agency():
    agency = Agency.get()
    if request.method == "POST":
        for field in TEXT_FIELDS:
            setattr(agency, field, form_str(request.form, field))
        agency.contract_terms = (request.form.get("contract_terms") or "").strip()
        agency.contract_terms_ar = (request.form.get("contract_terms_ar") or "").strip()
        agency.default_caution = form_float(request.form, "default_caution")
        errors = []
        prefixes = {}
        for field in ("contract_prefix", "engagement_prefix"):
            value = form_str(request.form, field).upper()
            if not re.fullmatch(r"[A-Z0-9]{1,10}", value):
                errors.append("Les préfixes doivent contenir 1 à 10 lettres ou chiffres.")
            prefixes[field] = value
        if prefixes.get("contract_prefix") == prefixes.get("engagement_prefix"):
            errors.append("Les préfixes des contrats et des engagements doivent être différents.")
        if not agency.name:
            errors.append("Le nom de l'agence est obligatoire.")
        if errors:
            db.session.rollback()
            for e in sorted(set(errors)):
                flash(e, "danger")
            return redirect(url_for("settings.agency"))
        upload = request.files.get("logo")
        if upload and upload.filename:
            try:
                save_logo(upload.stream)
            except (OSError, ValueError, Image.DecompressionBombError):
                db.session.rollback()
                flash("Le fichier du logo n'est pas une image valide (JPG ou PNG).", "danger")
                return redirect(url_for("settings.agency"))
        elif request.form.get("remove_logo") == "1" and logo_exists():
            remove_logo()
        agency.contract_prefix = prefixes["contract_prefix"]
        agency.engagement_prefix = prefixes["engagement_prefix"]
        agency.currency = agency.currency or "DH"
        db.session.commit()
        flash("Paramètres de l'agence enregistrés.", "success")
        return redirect(url_for("settings.agency"))
    return render_template("settings/agency.html")
