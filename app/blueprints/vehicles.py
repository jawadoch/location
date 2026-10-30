from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app

from ..extensions import db
from ..models import Vehicle, Contract, Engagement, VEHICLE_STATUSES, FUEL_TYPES
from ..utils import form_str, form_date, form_float, form_int, search_filter

bp = Blueprint("vehicles", __name__)


def apply_vehicle_form(vehicle, form):
    vehicle.brand = form_str(form, "brand")
    vehicle.model = form_str(form, "model")
    vehicle.plate = form_str(form, "plate").upper()
    vehicle.year = form_int(form, "year")
    vehicle.color = form_str(form, "color")
    vehicle.fuel = form_str(form, "fuel", "Diesel")
    vehicle.gearbox = form_str(form, "gearbox", "Manuelle")
    vehicle.mileage = form_int(form, "mileage", 0)
    vehicle.daily_rate = form_float(form, "daily_rate")
    status = form_str(form, "status", "disponible")
    vehicle.status = status if status in VEHICLE_STATUSES else "disponible"
    vehicle.insurance_expiry = form_date(form, "insurance_expiry")
    vehicle.technical_visit_expiry = form_date(form, "technical_visit_expiry")
    vehicle.notes = form_str(form, "notes")


def validate_vehicle(vehicle):
    errors = []
    if not vehicle.brand or not vehicle.model:
        errors.append("La marque et le modèle sont obligatoires.")
    if not vehicle.plate:
        errors.append("L'immatriculation est obligatoire.")
    elif Vehicle.query.filter(Vehicle.plate == vehicle.plate, Vehicle.id != vehicle.id).first():
        errors.append("Un véhicule avec cette immatriculation existe déjà.")
    if vehicle.daily_rate is None or vehicle.daily_rate < 0:
        errors.append("Le tarif journalier doit être positif.")
    return errors


def render_form(vehicle):
    return render_template(
        "vehicles/form.html", vehicle=vehicle, statuses=VEHICLE_STATUSES, fuels=FUEL_TYPES
    )


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    query = Vehicle.query
    if q:
        query = query.filter(search_filter([Vehicle.brand, Vehicle.model, Vehicle.plate], q))
    if status in VEHICLE_STATUSES:
        query = query.filter(Vehicle.status == status)
    pagination = query.order_by(Vehicle.brand, Vehicle.model).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "vehicles/list.html", pagination=pagination, q=q, status=status, statuses=VEHICLE_STATUSES
    )


@bp.route("/nouveau", methods=["GET", "POST"])
def create():
    vehicle = Vehicle(status="disponible", fuel="Diesel", gearbox="Manuelle", mileage=0, daily_rate=0)
    if request.method == "POST":
        apply_vehicle_form(vehicle, request.form)
        errors = validate_vehicle(vehicle)
        if not errors:
            db.session.add(vehicle)
            db.session.commit()
            flash("Véhicule enregistré.", "success")
            return redirect(url_for("vehicles.view", vehicle_id=vehicle.id))
        for e in errors:
            flash(e, "danger")
    return render_form(vehicle)


@bp.route("/<int:vehicle_id>")
def view(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id) or abort(404)
    contracts = vehicle.contracts.order_by(Contract.start_at.desc()).all()
    return render_template("vehicles/view.html", vehicle=vehicle, contracts=contracts)


@bp.route("/<int:vehicle_id>/modifier", methods=["GET", "POST"])
def edit(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id) or abort(404)
    if request.method == "POST":
        with db.session.no_autoflush:
            apply_vehicle_form(vehicle, request.form)
            errors = validate_vehicle(vehicle)
        if not errors:
            db.session.commit()
            flash("Véhicule mis à jour.", "success")
            return redirect(url_for("vehicles.view", vehicle_id=vehicle.id))
        db.session.rollback()
        for e in errors:
            flash(e, "danger")
        vehicle = Vehicle(id=vehicle_id)
        apply_vehicle_form(vehicle, request.form)
    return render_form(vehicle)


@bp.route("/<int:vehicle_id>/supprimer", methods=["POST"])
def delete(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id) or abort(404)
    label = f"{vehicle.label} ({vehicle.plate})"
    # Les documents gardent leur instantané du véhicule : on les détache au lieu de les supprimer
    kept = Contract.query.filter_by(vehicle_id=vehicle.id).update({"vehicle_id": None})
    Engagement.query.filter_by(vehicle_id=vehicle.id).update({"vehicle_id": None})
    db.session.delete(vehicle)
    db.session.commit()
    msg = f"Véhicule {label} supprimé."
    if kept:
        msg += f" Ses {kept} contrat(s) restent dans l'historique."
    flash(msg, "success")
    return redirect(url_for("vehicles.index"))
