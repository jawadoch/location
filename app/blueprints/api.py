from flask import Blueprint, jsonify, request

from ..models import Client
from .clients import search_clients

bp = Blueprint("api", __name__)


@bp.route("/clients")
def clients():
    """Autocomplétion : recherche de clients par nom, CIN, passeport ou téléphone."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    results = search_clients(q).order_by(Client.last_name).limit(10).all()
    return jsonify([c.to_dict() for c in results])
