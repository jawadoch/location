from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app

from ..extensions import db
from ..i18n import _
from ..models import Client, Contract, Engagement
from ..utils import form_str, form_date, search_filter

bp = Blueprint("clients", __name__)

CLIENT_SEARCH_COLUMNS = [
    Client.last_name, Client.first_name, Client.cin, Client.passport_no, Client.phone,
]


def search_clients(q):
    query = Client.query
    if q:
        terms = q.split()
        for term in terms:
            query = query.filter(search_filter(CLIENT_SEARCH_COLUMNS, term))
    return query


def apply_client_form(client, form):
    client.last_name = form_str(form, "last_name").upper()
    client.first_name = form_str(form, "first_name")
    client.nationality = form_str(form, "nationality")
    client.birth_date = form_date(form, "birth_date")
    client.cin = form_str(form, "cin").upper() or None
    client.cin_valid_until = form_date(form, "cin_valid_until")
    client.passport_no = form_str(form, "passport_no").upper() or None
    client.passport_issued_at = form_str(form, "passport_issued_at")
    client.license_no = form_str(form, "license_no").upper() or None
    client.license_date = form_date(form, "license_date")
    client.license_place = form_str(form, "license_place")
    client.address = form_str(form, "address")
    client.city = form_str(form, "city")
    client.phone = form_str(form, "phone") or None
    client.email = form_str(form, "email")
    client.notes = form_str(form, "notes")


def validate_client(client):
    errors = []
    if not client.last_name:
        errors.append(_("Le nom du client est obligatoire."))
    if not (client.cin or client.passport_no):
        errors.append(_("Renseignez au moins le N° CIN ou le N° de passeport."))
    for field, label in (("cin", "CIN"), ("passport_no", "passeport")):
        value = getattr(client, field)
        if value:
            other = Client.query.filter(getattr(Client, field) == value, Client.id != client.id).first()
            if other:
                errors.append(_("Un client avec ce N° {label} existe déjà : {name}.", label=_(label), name=other.full_name))
    return errors


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    pagination = search_clients(q).order_by(Client.last_name, Client.first_name).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("clients/list.html", pagination=pagination, q=q)


@bp.route("/nouveau", methods=["GET", "POST"])
def create():
    client = Client(nationality="Marocaine")
    if request.method == "POST":
        apply_client_form(client, request.form)
        errors = validate_client(client)
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            db.session.add(client)
            db.session.commit()
            flash(_("Client enregistré."), "success")
            next_url = request.args.get("next")
            if next_url == "contrat":
                return redirect(url_for("contracts.create", client_id=client.id))
            return redirect(url_for("clients.view", client_id=client.id))
    return render_template("clients/form.html", client=client)


@bp.route("/<int:client_id>")
def view(client_id):
    client = db.session.get(Client, client_id) or abort(404)
    contracts = client.contracts.order_by(Contract.created_at.desc()).all()
    engagements = client.engagements.order_by(Engagement.created_at.desc()).all()
    return render_template("clients/view.html", client=client, contracts=contracts, engagements=engagements)


@bp.route("/<int:client_id>/modifier", methods=["GET", "POST"])
def edit(client_id):
    client = db.session.get(Client, client_id) or abort(404)
    if request.method == "POST":
        with db.session.no_autoflush:
            apply_client_form(client, request.form)
            errors = validate_client(client)
        if errors:
            db.session.rollback()
            for e in errors:
                flash(e, "danger")
            client = Client(id=client_id)  # brouillon non enregistré pour réafficher la saisie
            apply_client_form(client, request.form)
        else:
            db.session.commit()
            flash(_("Fiche client mise à jour."), "success")
            return redirect(url_for("clients.view", client_id=client.id))
    return render_template("clients/form.html", client=client)


@bp.route("/<int:client_id>/supprimer", methods=["POST"])
def delete(client_id):
    client = db.session.get(Client, client_id) or abort(404)
    name = client.full_name
    # Les documents gardent leur instantané du client : on les détache au lieu de les supprimer
    kept = Contract.query.filter_by(client_id=client.id).update({"client_id": None})
    kept += Engagement.query.filter_by(client_id=client.id).update({"client_id": None})
    db.session.delete(client)
    db.session.commit()
    msg = _("Client {name} supprimé.", name=name)
    if kept:
        msg += " " + _("Ses {n} document(s) restent dans l'historique.", n=kept)
    flash(msg, "success")
    return redirect(url_for("clients.index"))
