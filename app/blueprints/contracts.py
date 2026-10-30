from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..i18n import _
from ..models import (
    Agency, Client, Contract, Engagement, Vehicle,
    CONTRACT_STATUSES, DOCUMENT_FLAGS, FUEL_LEVELS, PAYMENT_METHODS,
)
from ..pdf import pdf_response
from .conditions import conditions_context
from ..utils import (
    form_str, form_date, form_datetime, form_float, form_int, form_bool,
    next_number, rental_days, search_filter,
)

bp = Blueprint("contracts", __name__)

STR_FIELDS = [
    "client_last_name", "client_first_name", "client_nationality", "client_passport_issued_at",
    "client_license_place", "client_address", "client_phone",
    "driver2_name", "driver2_license_no", "driver2_license_place", "driver2_cin",
    "prolongation", "pickup_place", "return_place", "accessories",
    "changed_brand", "changed_plate", "notes",
]
UPPER_FIELDS = ["client_cin", "client_passport", "client_license_no"]
DATE_FIELDS = [
    "client_birth_date", "client_license_date", "driver2_license_date", "driver2_cin_date", "changed_date",
]
BOOL_FIELDS = ["washing"] + [flag for flag, _, _ in DOCUMENT_FLAGS]

# Colonnes copiées lors d'une duplication
CLONE_EXCLUDE = {"id", "number", "status", "source_id", "created_at", "updated_at"}

SEARCH_COLUMNS = [
    Contract.number, Contract.client_name, Contract.client_cin, Contract.client_passport,
    Contract.client_phone, Contract.vehicle_plate,
]


# ---------------------------------------------------------------- formulaire

def apply_contract_form(c, form):
    for name in STR_FIELDS:
        setattr(c, name, form_str(form, name))
    for name in UPPER_FIELDS:
        setattr(c, name, form_str(form, name).upper())
    for name in DATE_FIELDS:
        setattr(c, name, form_date(form, name))
    for name in BOOL_FIELDS:
        setattr(c, name, form_bool(form, name))

    c.client_last_name = c.client_last_name.upper()
    c.client_name = " ".join(p for p in [c.client_last_name, c.client_first_name] if p)
    c.client_id = form_int(form, "client_id")
    c.vehicle_id = form_int(form, "vehicle_id")
    c.driver2_name = c.driver2_name.upper()
    c.driver2_cin = c.driver2_cin.upper()
    c.driver2_license_no = c.driver2_license_no.upper()
    c.changed_plate = c.changed_plate.upper()

    c.start_at = form_datetime(form, "start_at")
    c.end_at = form_datetime(form, "end_at")
    c.km_start = form_int(form, "km_start")
    c.km_end = form_int(form, "km_end")
    fuel = form_str(form, "fuel_level", "Plein")
    c.fuel_level = fuel if fuel in FUEL_LEVELS else "Plein"
    payment = form_str(form, "payment_method", PAYMENT_METHODS[0])
    c.payment_method = payment if payment in PAYMENT_METHODS else PAYMENT_METHODS[0]
    status = form_str(form, "status", "en_cours")
    c.status = status if status in CONTRACT_STATUSES else "en_cours"

    c.daily_rate = form_float(form, "daily_rate")
    c.days = form_int(form, "days") or rental_days(c.start_at, c.end_at)
    c.amount = form_float(form, "amount")
    c.advance = form_float(form, "advance")
    c.caution = form_float(form, "caution")
    if not c.amount:
        c.amount = round(c.daily_rate * c.days, 2)


def validate_contract(c, is_new):
    errors = []
    if not c.client_last_name:
        errors.append(_("Le nom du client est obligatoire."))
    if not (c.client_cin or c.client_passport):
        errors.append(_("Renseignez le N° CIN ou le N° de passeport du client."))
    if not c.client_license_no:
        errors.append(_("Le N° de permis de conduire du client est obligatoire."))
    if not c.start_at or not c.end_at:
        errors.append(_("Les dates et heures de départ et de retour sont obligatoires."))
    elif c.end_at <= c.start_at:
        errors.append(_("La date de retour doit être postérieure à la date de départ."))
    if c.km_start is not None and c.km_end is not None and c.km_end < c.km_start:
        errors.append(_("Le kilométrage de retour ne peut pas être inférieur au kilométrage de départ."))
    if min(c.daily_rate, c.amount, c.advance, c.caution) < 0:
        errors.append(_("Les montants ne peuvent pas être négatifs."))

    vehicle = db.session.get(Vehicle, c.vehicle_id) if c.vehicle_id else None
    if vehicle is None:
        errors.append(_("Sélectionnez un véhicule."))
    else:
        if is_new and vehicle.status != "disponible":
            errors.append(_("Le véhicule {plate} est indisponible ({status}).", plate=vehicle.plate, status=_(vehicle.status_label)))
        if c.status == "en_cours" and c.start_at and c.end_at and c.end_at > c.start_at:
            overlap = Contract.query.filter(
                Contract.vehicle_id == vehicle.id,
                Contract.status == "en_cours",
                Contract.start_at < c.end_at,
                Contract.end_at > c.start_at,
            )
            if c.id:
                overlap = overlap.filter(Contract.id != c.id)
            other = overlap.first()
            if other:
                errors.append(
                    _("Le véhicule {plate} est déjà loué sur cette période (contrat {number}).",
                      plate=vehicle.plate, number=other.number)
                )

    if c.client_id:
        for field, attr, label in (("cin", "client_cin", "CIN"), ("passport_no", "client_passport", "passeport")):
            value = getattr(c, attr)
            if value:
                owner = Client.query.filter(getattr(Client, field) == value).first()
                if owner and owner.id != c.client_id:
                    errors.append(_("Le N° {label} {value} appartient au client {name}.", label=_(label), value=value, name=owner.full_name))
    return errors


def sync_client(c):
    """Associe le contrat à une fiche client existante (ou en crée une) et la met à jour."""
    client = db.session.get(Client, c.client_id) if c.client_id else None
    if client is None and c.client_cin:
        client = Client.query.filter_by(cin=c.client_cin).first()
    if client is None and c.client_passport:
        client = Client.query.filter_by(passport_no=c.client_passport).first()
    if client is None:
        client = Client(last_name=c.client_last_name)
        db.session.add(client)

    mapping = {
        "last_name": c.client_last_name,
        "first_name": c.client_first_name,
        "nationality": c.client_nationality,
        "birth_date": c.client_birth_date,
        "cin": c.client_cin or None,
        "passport_no": c.client_passport or None,
        "passport_issued_at": c.client_passport_issued_at,
        "license_no": c.client_license_no or None,
        "license_date": c.client_license_date,
        "license_place": c.client_license_place,
        "address": c.client_address,
        "phone": c.client_phone or None,
    }
    for attr, value in mapping.items():
        if value:
            setattr(client, attr, value)
    c.client = client


def snapshot_vehicle(c):
    vehicle = db.session.get(Vehicle, c.vehicle_id)
    c.vehicle_brand = vehicle.brand
    c.vehicle_model = vehicle.model
    c.vehicle_plate = vehicle.plate
    if not c.daily_rate:
        c.daily_rate = vehicle.daily_rate
        if not c.amount:
            c.amount = round(c.daily_rate * c.days, 2)


def update_vehicle_mileage(c):
    if c.km_end and c.vehicle and (c.vehicle.mileage or 0) < c.km_end:
        c.vehicle.mileage = c.km_end


def render_form(c, title, source=None):
    vehicles = Vehicle.query.order_by(Vehicle.brand, Vehicle.model).all()
    return render_template(
        "contracts/form.html",
        c=c,
        title=title,
        source=source,
        vehicles=vehicles,
        statuses=CONTRACT_STATUSES,
        document_flags=DOCUMENT_FLAGS,
        fuel_levels=FUEL_LEVELS,
        payment_methods=PAYMENT_METHODS,
    )


def save_new(c):
    """Insère le contrat avec un numéro unique (réessaie en cas de collision)."""
    for _ in range(5):
        with db.session.no_autoflush:
            prefix = Agency.get().contract_prefix or "CT"
            c.number = next_number(Contract, prefix)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            db.session.add(c)
    return False


def default_contract():
    start = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return Contract(
        status="en_cours",
        client_nationality="Marocaine",
        start_at=start,
        end_at=start + timedelta(days=1),
        days=1,
        daily_rate=0,
        amount=0,
        advance=0,
        caution=Agency.get().default_caution or 0,
        fuel_level="Plein",
        payment_method=PAYMENT_METHODS[0],
        washing=False,
        doc_carte_grise=True,
        doc_assurance=True,
        doc_vignette=True,
        doc_visite=True,
        doc_autorisation=False,
        doc_contrat=True,
    )


def prefill_client(c, client):
    c.client_id = client.id
    c.client_last_name = client.last_name
    c.client_first_name = client.first_name
    c.client_nationality = client.nationality
    c.client_birth_date = client.birth_date
    c.client_cin = client.cin or ""
    c.client_passport = client.passport_no or ""
    c.client_passport_issued_at = client.passport_issued_at
    c.client_license_no = client.license_no or ""
    c.client_license_date = client.license_date
    c.client_license_place = client.license_place
    c.client_address = " ".join(p for p in [client.address, client.city] if p)
    c.client_phone = client.phone or ""


# ---------------------------------------------------------------- routes

@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    query = Contract.query
    if q:
        query = query.filter(search_filter(SEARCH_COLUMNS, q))
    if status in CONTRACT_STATUSES:
        query = query.filter(Contract.status == status)
    pagination = query.order_by(Contract.created_at.desc(), Contract.id.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "contracts/list.html", pagination=pagination, q=q, status=status, statuses=CONTRACT_STATUSES
    )


@bp.route("/nouveau", methods=["GET", "POST"])
def create():
    c = default_contract()
    source = None
    if request.method == "POST":
        source_id = form_int(request.form, "source_id")
        source = db.session.get(Contract, source_id) if source_id else None
        apply_contract_form(c, request.form)
        c.source_id = source.id if source else None
        errors = validate_contract(c, is_new=True)
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            with db.session.no_autoflush:
                db.session.add(c)
                sync_client(c)
                snapshot_vehicle(c)
                update_vehicle_mileage(c)
            if save_new(c):
                flash(_("Contrat {number} enregistré.", number=c.number), "success")
                return redirect(url_for("contracts.view", contract_id=c.id))
            flash(_("Impossible de générer un numéro de contrat unique, réessayez."), "danger")
    else:
        client_id = request.args.get("client_id", type=int)
        vehicle_id = request.args.get("vehicle_id", type=int)
        client = db.session.get(Client, client_id) if client_id else None
        if client:
            prefill_client(c, client)
        vehicle = db.session.get(Vehicle, vehicle_id) if vehicle_id else None
        if vehicle:
            c.vehicle_id = vehicle.id
            c.daily_rate = vehicle.daily_rate
            c.amount = vehicle.daily_rate * c.days
            c.km_start = vehicle.mileage
    return render_form(c, _("Nouveau contrat"), source)


@bp.route("/<int:contract_id>")
def view(contract_id):
    c = db.session.get(Contract, contract_id) or abort(404)
    verso = request.args.get("verso") == "1"
    return render_template(
        "contracts/view.html", c=c, document_flags=DOCUMENT_FLAGS, fuel_levels=FUEL_LEVELS,
        verso=verso, **(conditions_context() if verso else {}),
    )


@bp.route("/<int:contract_id>/pdf")
def pdf(contract_id):
    c = db.session.get(Contract, contract_id) or abort(404)
    verso = request.args.get("verso") == "1"
    return pdf_response(
        "contracts/pdf.html",
        f"Contrat-{c.number}{'-recto-verso' if verso else ''}.pdf",
        inline=request.args.get("inline") == "1",
        c=c,
        document_flags=DOCUMENT_FLAGS,
        fuel_levels=FUEL_LEVELS,
        verso=verso,
        **(conditions_context() if verso else {}),
    )


@bp.route("/<int:contract_id>/modifier", methods=["GET", "POST"])
def edit(contract_id):
    c = db.session.get(Contract, contract_id) or abort(404)
    if request.method == "POST":
        previous_vehicle = c.vehicle_id
        with db.session.no_autoflush:
            apply_contract_form(c, request.form)
            errors = validate_contract(c, is_new=False)
        if errors:
            db.session.rollback()
            for e in errors:
                flash(e, "danger")
            draft = Contract(id=contract_id, number=c.number)
            apply_contract_form(draft, request.form)
            return render_form(draft, _("Modifier le contrat {number}", number=draft.number))
        sync_client(c)
        if c.vehicle_id != previous_vehicle:
            snapshot_vehicle(c)
        update_vehicle_mileage(c)
        db.session.commit()
        flash(_("Contrat mis à jour."), "success")
        return redirect(url_for("contracts.view", contract_id=c.id))
    return render_form(c, _("Modifier le contrat {number}", number=c.number))


@bp.route("/<int:contract_id>/dupliquer")
def duplicate(contract_id):
    source = db.session.get(Contract, contract_id) or abort(404)
    c = default_contract()
    for column in Contract.__table__.columns:
        if column.name not in CLONE_EXCLUDE:
            setattr(c, column.name, getattr(source, column.name))

    # Nouvelle période de même durée, à partir de maintenant
    duration = source.end_at - source.start_at
    c.start_at = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    c.end_at = c.start_at + duration
    c.status = "en_cours"
    c.km_start = source.km_end if source.km_end is not None else (
        source.vehicle.mileage if source.vehicle else source.km_start
    )
    c.km_end = None
    c.advance = 0
    c.prolongation = ""
    c.changed_brand = c.changed_plate = ""
    c.changed_date = None
    c.source_id = source.id
    flash(
        _("Duplication du contrat {number} : vérifiez les dates, le véhicule et les montants. "
          "Un nouveau numéro sera attribué ; l'original reste inchangé.", number=source.number),
        "info",
    )
    return render_form(c, _("Dupliquer le contrat {number}", number=source.number), source)


@bp.route("/<int:contract_id>/cloturer", methods=["POST"])
def close(contract_id):
    c = db.session.get(Contract, contract_id) or abort(404)
    km_end = form_int(request.form, "km_end")
    if km_end is not None:
        if c.km_start is not None and km_end < c.km_start:
            flash(_("Le kilométrage de retour est inférieur au kilométrage de départ."), "danger")
            return redirect(url_for("contracts.view", contract_id=c.id))
        c.km_end = km_end
    fuel = form_str(request.form, "fuel_level")
    if fuel in FUEL_LEVELS:
        c.fuel_level = fuel
    c.status = "termine"
    update_vehicle_mileage(c)
    db.session.commit()
    flash(_("Contrat {number} clôturé : véhicule restitué.", number=c.number), "success")
    return redirect(url_for("contracts.view", contract_id=c.id))


@bp.route("/<int:contract_id>/supprimer", methods=["POST"])
def delete(contract_id):
    c = db.session.get(Contract, contract_id) or abort(404)
    number = c.number
    # Les engagements liés et les copies dupliquées sont conservés (le N° reste écrit sur l'engagement)
    Engagement.query.filter_by(contract_id=c.id).update({"contract_id": None})
    Contract.query.filter_by(source_id=c.id).update({"source_id": None})
    db.session.delete(c)
    db.session.commit()
    flash(_("Contrat {number} supprimé définitivement.", number=number), "success")
    return redirect(url_for("contracts.index"))


@bp.route("/<int:contract_id>/annuler", methods=["POST"])
def cancel(contract_id):
    c = db.session.get(Contract, contract_id) or abort(404)
    c.status = "annule"
    db.session.commit()
    flash(_("Contrat {number} annulé (il reste dans l'historique).", number=c.number), "warning")
    return redirect(url_for("contracts.view", contract_id=c.id))
