from flask import Blueprint, render_template, request, redirect, url_for, flash

from ..conditions import default_conditions, parse_blocks
from ..extensions import db
from ..i18n import _
from ..models import Agency, GeneralConditions
from ..pdf import pdf_response
from ..utils import form_str

bp = Blueprint("conditions", __name__)


def conditions_context():
    """Variables utilisées par les feuilles des conditions générales (écran et PDF)."""
    cg = GeneralConditions.get()
    return {
        "cg": cg,
        "cg_fr": parse_blocks(cg.body_fr),
        "cg_ar": parse_blocks(cg.body_ar),
    }


@bp.route("/")
def view():
    return render_template("conditions/view.html", **conditions_context())


@bp.route("/pdf")
def pdf():
    return pdf_response(
        "conditions/pdf.html",
        "Conditions-generales.pdf",
        inline=request.args.get("inline") == "1",
        **conditions_context(),
    )


@bp.route("/modifier", methods=["GET", "POST"])
def edit():
    cg = GeneralConditions.get()
    if request.method == "POST":
        cg.title_fr = form_str(request.form, "title_fr")
        cg.title_ar = form_str(request.form, "title_ar")
        cg.body_fr = (request.form.get("body_fr") or "").strip()
        cg.body_ar = (request.form.get("body_ar") or "").strip()
        if not all([cg.title_fr, cg.title_ar, cg.body_fr, cg.body_ar]):
            db.session.rollback()
            flash(_("Les titres et les textes en français et en arabe sont obligatoires."), "danger")
            cg = GeneralConditions(
                title_fr=form_str(request.form, "title_fr"), title_ar=form_str(request.form, "title_ar"),
                body_fr=request.form.get("body_fr") or "", body_ar=request.form.get("body_ar") or "",
            )
            return render_template("conditions/form.html", cg=cg)
        db.session.commit()
        flash(_("Conditions générales enregistrées."), "success")
        return redirect(url_for("conditions.view"))
    return render_template("conditions/form.html", cg=cg)


@bp.route("/reinitialiser", methods=["POST"])
def reset():
    cg = GeneralConditions.get()
    for field, value in default_conditions(Agency.get().city).items():
        setattr(cg, field, value)
    db.session.commit()
    flash(_("Texte par défaut des conditions générales rétabli."), "success")
    return redirect(url_for("conditions.view"))
