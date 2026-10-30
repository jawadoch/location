from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Agency, Client, Contract, Engagement, EngagementTemplate, Vehicle
from ..pdf import pdf_response
from ..utils import (
    form_str, form_date, form_float, form_int, form_bool,
    next_number, search_filter, engagement_context, render_placeholders, PLACEHOLDERS,
)

bp = Blueprint("engagements", __name__)

SEARCH_COLUMNS = [
    Engagement.number, Engagement.client_name, Engagement.client_cin,
    Engagement.client_passport, Engagement.client_phone, Engagement.contract_number,
    Engagement.title,
]

CLONE_EXCLUDE = {"id", "number", "source_id", "created_at", "updated_at", "body"}


# ---------------------------------------------------------------- formulaire

def apply_engagement_form(e, form):
    e.template_id = form_int(form, "template_id")
    e.client_id = form_int(form, "client_id")
    e.vehicle_id = form_int(form, "vehicle_id")
    e.title = form_str(form, "title")
    e.body_source = (form.get("body_source") or "").strip()
    e.doc_date = form_date(form, "doc_date") or date.today()
    e.place = form_str(form, "place")
    amount = form_str(form, "amount")
    e.amount = form_float(form, "amount") if amount else None
    e.start_date = form_date(form, "start_date")
    e.end_date = form_date(form, "end_date")
    e.client_name = form_str(form, "client_name").upper()
    e.client_cin = form_str(form, "client_cin").upper()
    e.client_passport = form_str(form, "client_passport").upper()
    e.client_license_no = form_str(form, "client_license_no").upper()
    e.client_address = form_str(form, "client_address")
    e.client_phone = form_str(form, "client_phone")
    e.client_nationality = form_str(form, "client_nationality")
    e.vehicle_label = form_str(form, "vehicle_label")
    e.vehicle_plate = form_str(form, "vehicle_plate").upper()
    e.contract_number = form_str(form, "contract_number").upper()


def validate_engagement(e):
    errors = []
    if not e.title:
        errors.append("Le titre est obligatoire.")
    if not e.body_source:
        errors.append("Le texte de l'engagement est obligatoire.")
    if not e.client_name:
        errors.append("Le nom du client est obligatoire.")
    if e.contract_number and not Contract.query.filter_by(number=e.contract_number).first():
        errors.append(f"Aucun contrat ne porte le numéro {e.contract_number}.")
    if e.amount is not None and e.amount < 0:
        errors.append("Le montant ne peut pas être négatif.")
    return errors


def link_and_render(e):
    """Lie les fiches existantes, complète les instantanés et fige le texte final."""
    contract = Contract.query.filter_by(number=e.contract_number).first() if e.contract_number else None
    e.contract_id = contract.id if contract else None
    if contract:
        e.client_id = e.client_id or contract.client_id
        e.vehicle_id = e.vehicle_id or contract.vehicle_id
        e.vehicle_label = e.vehicle_label or contract.vehicle_label
        e.vehicle_plate = e.vehicle_plate or contract.vehicle_plate
        e.start_date = e.start_date or contract.start_at.date()
        e.end_date = e.end_date or contract.end_at.date()

    client = db.session.get(Client, e.client_id) if e.client_id else None
    if client is None and e.client_cin:
        client = Client.query.filter_by(cin=e.client_cin).first()
    e.client_id = client.id if client else None

    vehicle = db.session.get(Vehicle, e.vehicle_id) if e.vehicle_id else None
    if vehicle:
        e.vehicle_label = e.vehicle_label or vehicle.label
        e.vehicle_plate = e.vehicle_plate or vehicle.plate
    else:
        e.vehicle_id = None

    if e.template_id and not db.session.get(EngagementTemplate, e.template_id):
        e.template_id = None
    e.body = render_placeholders(e.body_source, engagement_context(e, Agency.get()))


def prefill_from_client(e, client):
    e.client_id = client.id
    e.client_name = client.full_name
    e.client_cin = client.cin or ""
    e.client_passport = client.passport_no or ""
    e.client_license_no = client.license_no or ""
    e.client_address = " ".join(p for p in [client.address, client.city] if p)
    e.client_phone = client.phone or ""
    e.client_nationality = client.nationality or ""


def prefill_from_contract(e, c):
    e.contract_number = c.number
    e.client_id = c.client_id
    e.client_name = c.client_name
    e.client_cin = c.client_cin
    e.client_passport = c.client_passport
    e.client_license_no = c.client_license_no
    e.client_address = c.client_address
    e.client_phone = c.client_phone
    e.client_nationality = c.client_nationality
    e.vehicle_id = c.vehicle_id
    e.vehicle_label = c.vehicle_label
    e.vehicle_plate = c.vehicle_plate
    e.start_date = c.start_at.date()
    e.end_date = c.end_at.date()
    e.amount = c.caution or None


def render_form(e, title, source=None):
    templates = EngagementTemplate.query.filter_by(active=True).order_by(EngagementTemplate.name).all()
    if e.template_id and all(t.id != e.template_id for t in templates):
        tpl = db.session.get(EngagementTemplate, e.template_id)
        if tpl:
            templates.append(tpl)
    vehicles = Vehicle.query.order_by(Vehicle.brand, Vehicle.model).all()
    return render_template(
        "engagements/form.html",
        e=e,
        title=title,
        source=source,
        templates=templates,
        vehicles=vehicles,
        placeholders=PLACEHOLDERS,
    )


def save_new(e):
    for _ in range(5):
        with db.session.no_autoflush:
            prefix = Agency.get().engagement_prefix or "EG"
            e.number = next_number(Engagement, prefix)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            db.session.add(e)
    return False


# ---------------------------------------------------------------- routes

@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Engagement.query
    if q:
        query = query.filter(search_filter(SEARCH_COLUMNS, q))
    pagination = query.order_by(Engagement.created_at.desc(), Engagement.id.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("engagements/list.html", pagination=pagination, q=q)


@bp.route("/nouveau", methods=["GET", "POST"])
def create():
    agency = Agency.get()
    e = Engagement(doc_date=date.today(), place=agency.city, title="", body_source="")
    source = None
    if request.method == "POST":
        source_id = form_int(request.form, "source_id")
        source = db.session.get(Engagement, source_id) if source_id else None
        apply_engagement_form(e, request.form)
        e.source_id = source.id if source else None
        errors = validate_engagement(e)
        if errors:
            for msg in errors:
                flash(msg, "danger")
        else:
            with db.session.no_autoflush:
                link_and_render(e)
                db.session.add(e)
            if save_new(e):
                flash(f"Engagement {e.number} enregistré.", "success")
                return redirect(url_for("engagements.view", engagement_id=e.id))
            flash("Impossible de générer un numéro unique, réessayez.", "danger")
    else:
        template_id = request.args.get("template_id", type=int)
        tpl = db.session.get(EngagementTemplate, template_id) if template_id else None
        tpl = tpl or EngagementTemplate.query.filter_by(active=True).order_by(EngagementTemplate.name).first()
        if tpl:
            e.template_id, e.title, e.body_source = tpl.id, tpl.title, tpl.body
        contract_id = request.args.get("contract_id", type=int)
        contract = db.session.get(Contract, contract_id) if contract_id else None
        client_id = request.args.get("client_id", type=int)
        client = db.session.get(Client, client_id) if client_id else None
        if contract:
            prefill_from_contract(e, contract)
        elif client:
            prefill_from_client(e, client)
    return render_form(e, "Nouvel engagement", source)


@bp.route("/<int:engagement_id>")
def view(engagement_id):
    e = db.session.get(Engagement, engagement_id) or abort(404)
    return render_template("engagements/view.html", e=e)


@bp.route("/<int:engagement_id>/pdf")
def pdf(engagement_id):
    e = db.session.get(Engagement, engagement_id) or abort(404)
    return pdf_response(
        "engagements/pdf.html",
        f"Engagement-{e.number}.pdf",
        inline=request.args.get("inline") == "1",
        e=e,
    )


@bp.route("/<int:engagement_id>/modifier", methods=["GET", "POST"])
def edit(engagement_id):
    e = db.session.get(Engagement, engagement_id) or abort(404)
    if request.method == "POST":
        with db.session.no_autoflush:
            apply_engagement_form(e, request.form)
            errors = validate_engagement(e)
            if not errors:
                link_and_render(e)
        if not errors:
            db.session.commit()
            flash("Engagement mis à jour.", "success")
            return redirect(url_for("engagements.view", engagement_id=e.id))
        db.session.rollback()
        for msg in errors:
            flash(msg, "danger")
        draft = Engagement(id=engagement_id, number=e.number)
        apply_engagement_form(draft, request.form)
        return render_form(draft, f"Modifier l'engagement {draft.number}")
    return render_form(e, f"Modifier l'engagement {e.number}")


@bp.route("/<int:engagement_id>/dupliquer")
def duplicate(engagement_id):
    source = db.session.get(Engagement, engagement_id) or abort(404)
    e = Engagement()
    for column in Engagement.__table__.columns:
        if column.name not in CLONE_EXCLUDE:
            setattr(e, column.name, getattr(source, column.name))
    e.doc_date = date.today()
    e.source_id = source.id
    flash(
        f"Duplication de l'engagement {source.number} : modifiez les informations utiles. "
        "Un nouveau numéro sera attribué ; l'original reste inchangé.",
        "info",
    )
    return render_form(e, f"Dupliquer l'engagement {source.number}", source)


# ---------------------------------------------------------------- modèles

@bp.route("/modeles")
def templates():
    items = EngagementTemplate.query.order_by(EngagementTemplate.active.desc(), EngagementTemplate.name).all()
    return render_template("engagements/templates.html", items=items)


def apply_template_form(tpl, form):
    tpl.name = form_str(form, "name")
    tpl.title = form_str(form, "title")
    tpl.body = (form.get("body") or "").strip()
    tpl.active = form_bool(form, "active")


def render_template_form(tpl):
    return render_template("engagements/template_form.html", tpl=tpl, placeholders=PLACEHOLDERS)


@bp.route("/modeles/nouveau", methods=["GET", "POST"])
def template_create():
    tpl = EngagementTemplate(active=True, name="", title="", body="")
    if request.method == "POST":
        apply_template_form(tpl, request.form)
        if tpl.name and tpl.title and tpl.body:
            db.session.add(tpl)
            db.session.commit()
            flash("Modèle enregistré.", "success")
            return redirect(url_for("engagements.templates"))
        flash("Le nom, le titre et le texte sont obligatoires.", "danger")
    return render_template_form(tpl)


@bp.route("/modeles/<int:template_id>/modifier", methods=["GET", "POST"])
def template_edit(template_id):
    tpl = db.session.get(EngagementTemplate, template_id) or abort(404)
    if request.method == "POST":
        apply_template_form(tpl, request.form)
        if tpl.name and tpl.title and tpl.body:
            db.session.commit()
            flash("Modèle mis à jour (les engagements déjà créés ne changent pas).", "success")
            return redirect(url_for("engagements.templates"))
        db.session.rollback()
        flash("Le nom, le titre et le texte sont obligatoires.", "danger")
        tpl = EngagementTemplate(id=template_id)
        apply_template_form(tpl, request.form)
    return render_template_form(tpl)
