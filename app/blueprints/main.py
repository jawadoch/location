import io
from datetime import datetime, date, timedelta

from flask import Blueprint, abort, redirect, render_template, request, send_file, url_for
from sqlalchemy import func

from ..extensions import db
from ..i18n import COOKIE, LANGUAGES
from ..logo import logo_path
from ..models import Client, Vehicle, Contract, Engagement

bp = Blueprint("main", __name__)


@bp.route("/langue/<code>")
def set_language(code):
    """Change la langue de l'interface et revient à la page précédente."""
    target = request.referrer or url_for("main.dashboard")
    if not target.startswith(request.host_url):
        target = url_for("main.dashboard")
    response = redirect(target)
    if code in LANGUAGES:
        response.set_cookie(COOKIE, code, max_age=60 * 60 * 24 * 365 * 5, samesite="Lax")
    return response


@bp.route("/logo.png")
def logo():
    path = logo_path()
    if path is None:
        abort(404)
    # Lu en mémoire : sous Windows, un fichier resté ouvert ne pourrait plus être remplacé
    with open(path, "rb") as f:
        data = io.BytesIO(f.read())
    return send_file(data, mimetype="image/png", max_age=0)


@bp.route("/")
def dashboard():
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    active_q = Contract.query.filter(Contract.status == "en_cours")
    rented_ids = {
        c.vehicle_id
        for c in active_q.filter(Contract.start_at <= now, Contract.end_at >= now).all()
        if c.vehicle_id
    }
    vehicles_total = Vehicle.query.count()
    vehicles_available = Vehicle.query.filter(
        Vehicle.status == "disponible", ~Vehicle.id.in_(list(rented_ids) or [0])
    ).count()

    month_contracts = Contract.query.filter(
        Contract.status != "annule", Contract.created_at >= month_start
    )
    revenue_month = (
        db.session.query(func.coalesce(func.sum(Contract.amount), 0))
        .filter(Contract.status != "annule", Contract.created_at >= month_start)
        .scalar()
    )
    outstanding = (
        db.session.query(func.coalesce(func.sum(Contract.amount - Contract.advance), 0))
        .filter(Contract.status != "annule", Contract.amount > Contract.advance)
        .scalar()
    )

    stats = {
        "clients": Client.query.count(),
        "vehicles": vehicles_total,
        "vehicles_available": vehicles_available,
        "vehicles_rented": len(rented_ids),
        "contracts_active": active_q.count(),
        "contracts_month": month_contracts.count(),
        "revenue_month": revenue_month,
        "outstanding": outstanding,
        "engagements": Engagement.query.count(),
    }

    upcoming_returns = (
        active_q.filter(Contract.end_at <= now + timedelta(days=3))
        .order_by(Contract.end_at)
        .limit(10)
        .all()
    )
    recent_contracts = Contract.query.order_by(Contract.created_at.desc()).limit(8).all()
    soon = date.today() + timedelta(days=30)
    expiring = Vehicle.query.filter(
        db.or_(Vehicle.insurance_expiry <= soon, Vehicle.technical_visit_expiry <= soon)
    ).all()

    return render_template(
        "dashboard.html",
        stats=stats,
        upcoming_returns=upcoming_returns,
        recent_contracts=recent_contracts,
        expiring=expiring,
        now=now,
        today=date.today(),
    )
