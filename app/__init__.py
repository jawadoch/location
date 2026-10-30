import os

from flask import Flask
from markupsafe import Markup, escape

from .config import Config, INSTANCE_DIR
from .extensions import db, csrf
from .i18n import _, get_lang, is_rtl, js_texts, LANGUAGES
from .utils import fmt_date, fmt_money, is_arabic


def create_app(config_class=Config):
    app = Flask(__name__, instance_path=INSTANCE_DIR)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from .blueprints.main import bp as main_bp
    from .blueprints.clients import bp as clients_bp
    from .blueprints.vehicles import bp as vehicles_bp
    from .blueprints.contracts import bp as contracts_bp
    from .blueprints.engagements import bp as engagements_bp
    from .blueprints.settings import bp as settings_bp
    from .blueprints.api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(vehicles_bp, url_prefix="/vehicules")
    app.register_blueprint(contracts_bp, url_prefix="/contrats")
    app.register_blueprint(engagements_bp, url_prefix="/engagements")
    app.register_blueprint(settings_bp, url_prefix="/parametres")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.template_filter("date_fr")
    def _date_fr(value):
        return fmt_date(value)

    @app.template_filter("money")
    def _money(value, currency=None):
        from .models import Agency

        return fmt_money(value or 0, currency if currency is not None else Agency.get().currency)

    @app.template_filter("iso")
    def _iso(value, with_time=False):
        if not value:
            return ""
        return value.strftime("%Y-%m-%dT%H:%M" if with_time else "%Y-%m-%d")

    @app.template_filter("ltr")
    def _ltr(value):
        """Isole une valeur de gauche à droite (plaque, date, téléphone) dans l'interface arabe."""
        if value in (None, ""):
            return ""
        return Markup('<bdi dir="ltr">') + escape(value) + Markup("</bdi>")

    @app.template_test("arabic")
    def _is_arabic(value):
        return is_arabic(value)

    app.jinja_env.globals["_"] = _

    @app.context_processor
    def inject_agency():
        from .logo import logo_url
        from .models import Agency

        return {
            "agency": Agency.get(),
            "logo_url": logo_url(),
            "lang": get_lang(),
            "rtl": is_rtl(),
            "languages": LANGUAGES,
            "js_texts": js_texts(),
        }

    with app.app_context():
        from .seed import init_db

        init_db()

    return app
