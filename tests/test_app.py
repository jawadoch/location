import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Client, Contract, Engagement, Vehicle


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def vehicle(app):
    with app.app_context():
        v = Vehicle(brand="Dacia", model="Logan", plate="12345-A-6", daily_rate=300, mileage=50000)
        db.session.add(v)
        db.session.commit()
        return v.id


def contract_form(vehicle_id, **overrides):
    data = {
        "client_last_name": "Alaoui",
        "client_first_name": "Karim",
        "client_nationality": "Marocaine",
        "client_cin": "ab123456",
        "client_license_no": "11/223344",
        "client_phone": "0612345678",
        "client_address": "12 rue Hassan II, Laâyoune",
        "vehicle_id": str(vehicle_id),
        "start_at": "2026-11-02T10:00",
        "end_at": "2026-11-05T09:00",
        "daily_rate": "300",
        "days": "",
        "amount": "",
        "advance": "400",
        "caution": "5000",
        "km_start": "50000",
        "fuel_level": "Plein",
        "payment_method": "Espèces",
        "doc_carte_grise": "1",
        "doc_assurance": "1",
    }
    data.update(overrides)
    return data


def test_pages_load(client, vehicle):
    for url in ["/", "/clients/", "/clients/nouveau", "/vehicules/", "/vehicules/nouveau",
                "/contrats/", "/contrats/nouveau", "/engagements/", "/engagements/nouveau",
                "/engagements/modeles", "/engagements/modeles/nouveau", "/parametres/"]:
        resp = client.get(url)
        assert resp.status_code == 200, url


def test_client_crud_and_search(client, app):
    resp = client.post("/clients/nouveau", data={
        "last_name": "Bennani", "first_name": "Sara", "cin": "x998877", "phone": "0600000001",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "BENNANI Sara".encode() in resp.data
    # doublon CIN refusé
    resp = client.post("/clients/nouveau", data={"last_name": "Autre", "cin": "X998877"}, follow_redirects=True)
    assert "existe déjà".encode() in resp.data
    with app.app_context():
        assert Client.query.count() == 1
        cid = Client.query.first().id
    for q in ["benn", "X998877", "0600000001"]:
        assert b"BENNANI" in client.get(f"/clients/?q={q}").data
    api = client.get("/api/clients?q=sara").get_json()
    assert api[0]["cin"] == "X998877"
    resp = client.post(f"/clients/{cid}/modifier", data={"last_name": "Bennani", "first_name": "Sara", "cin": "X998877", "city": "Rabat"}, follow_redirects=True)
    assert b"Rabat" in resp.data


def test_vehicle_unique_plate(client, vehicle, app):
    resp = client.post("/vehicules/nouveau", data={"brand": "Renault", "model": "Clio", "plate": "12345-a-6", "daily_rate": "250"}, follow_redirects=True)
    assert "existe déjà".encode() in resp.data
    with app.app_context():
        assert Vehicle.query.count() == 1


def test_contract_creation_snapshot_and_client_autocreate(client, app, vehicle):
    resp = client.post("/contrats/nouveau", data=contract_form(vehicle), follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        c = Contract.query.one()
        assert c.number.startswith("CT-") and c.number.endswith("-0001")
        assert c.days == 3  # 2 j 23 h → 3 jours entamés
        assert c.amount == 900
        assert c.remaining == 500
        assert c.client_name == "ALAOUI Karim"
        assert c.client_cin == "AB123456"
        assert c.vehicle_plate == "12345-A-6"
        assert c.client is not None and c.client.cin == "AB123456"
        # l'instantané ne change pas si la fiche client ou véhicule change
        c.client.last_name = "MODIFIE"
        c.vehicle.plate = "99999-B-1"
        db.session.commit()
        c = db.session.get(Contract, c.id)
        assert c.client_name == "ALAOUI Karim" and c.vehicle_plate == "12345-A-6"


def test_contract_reuses_existing_client(client, app, vehicle):
    client.post("/clients/nouveau", data={"last_name": "Alaoui", "first_name": "Karim", "cin": "AB123456"})
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        assert Client.query.count() == 1
        assert Contract.query.one().client.phone == "0612345678"


def test_contract_overlap_rejected(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    resp = client.post("/contrats/nouveau", data=contract_form(vehicle, start_at="2026-11-04T10:00", end_at="2026-11-06T10:00"), follow_redirects=True)
    assert "déjà loué".encode() in resp.data
    with app.app_context():
        assert Contract.query.count() == 1


def test_contract_validation(client, app, vehicle):
    resp = client.post("/contrats/nouveau", data=contract_form(vehicle, end_at="2026-11-01T10:00", client_license_no=""), follow_redirects=True)
    assert "postérieure".encode() in resp.data
    assert "permis".encode() in resp.data
    with app.app_context():
        assert Contract.query.count() == 0


def test_duplicate_keeps_original(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        original = Contract.query.one()
        oid, onumber = original.id, original.number
    page = client.get(f"/contrats/{oid}/dupliquer")
    assert page.status_code == 200
    assert b"ALAOUI" in page.data and f'name="source_id" value="{oid}"'.encode() in page.data
    data = contract_form(vehicle, start_at="2026-12-01T10:00", end_at="2026-12-03T10:00", daily_rate="350", source_id=str(oid))
    client.post("/contrats/nouveau", data=data)
    with app.app_context():
        assert Contract.query.count() == 2
        orig = db.session.get(Contract, oid)
        copy = Contract.query.filter(Contract.id != oid).one()
        assert orig.number == onumber and orig.daily_rate == 300
        assert copy.number != onumber and copy.number.endswith("-0002")
        assert copy.source_id == oid and copy.amount == 700


def test_contract_edit_close_and_search(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        c = Contract.query.one()
        cid, number = c.id, c.number
    resp = client.post(f"/contrats/{cid}/modifier", data=contract_form(vehicle, advance="900", status="en_cours"), follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post(f"/contrats/{cid}/cloturer", data={"km_end": "50800", "fuel_level": "1/2"}, follow_redirects=True)
    assert "clôturé".encode() in resp.data
    with app.app_context():
        c = db.session.get(Contract, cid)
        assert c.status == "termine" and c.remaining == 0 and c.km_end == 50800
        assert c.vehicle.mileage == 50800
    for q in [number, "alaoui", "AB123456", "12345-A"]:
        assert number.encode() in client.get(f"/contrats/?q={q}").data


def test_contract_view_and_pdf(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        cid = Contract.query.one().id
    view = client.get(f"/contrats/{cid}")
    assert view.status_code == 200 and b"ALAOUI Karim" in view.data
    pdf = client.get(f"/contrats/{cid}/pdf")
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"
    assert pdf.data.startswith(b"%PDF")
    assert "attachment" in pdf.headers["Content-Disposition"]


def test_engagement_flow(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        c = Contract.query.one()
        cid, cnumber = c.id, c.number
    page = client.get(f"/engagements/nouveau?contract_id={cid}")
    assert b"ALAOUI Karim" in page.data
    resp = client.post("/engagements/nouveau", data={
        "title": "ENGAGEMENT TEST",
        "body_source": "Je soussigné {{ client_nom }}, CIN {{ client_cin }}, véhicule {{ immatriculation }}, {{ inconnu }}.",
        "client_name": "Alaoui Karim",
        "client_cin": "AB123456",
        "contract_number": cnumber,
        "doc_date": "2026-11-02",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        e = Engagement.query.one()
        eid = e.id
        assert e.number.startswith("EG-")
        assert e.body == "Je soussigné ALAOUI KARIM, CIN AB123456, véhicule 12345-A-6, {{ inconnu }}."
        assert e.contract_id == cid and e.client_id is not None
    # duplication : nouveau numéro, original intact
    dup = client.get(f"/engagements/{eid}/dupliquer")
    assert b"{{ client_nom }}" in dup.data
    client.post("/engagements/nouveau", data={
        "title": "ENGAGEMENT TEST", "body_source": "Texte {{ client_nom }}", "client_name": "Autre Client",
        "source_id": str(eid),
    })
    with app.app_context():
        assert Engagement.query.count() == 2
        assert db.session.get(Engagement, eid).body.startswith("Je soussigné ALAOUI")
        copy = Engagement.query.filter(Engagement.id != eid).one()
        assert copy.source_id == eid and copy.body == "Texte AUTRE CLIENT"
    assert b"ALAOUI" in client.get("/engagements/?q=ab123456").data
    pdf = client.get(f"/engagements/{eid}/pdf")
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")


def test_engagement_unknown_contract_rejected(client, app):
    resp = client.post("/engagements/nouveau", data={
        "title": "T", "body_source": "x", "client_name": "X", "contract_number": "CT-1999-0001",
    }, follow_redirects=True)
    assert "Aucun contrat".encode() in resp.data
    with app.app_context():
        assert Engagement.query.count() == 0


def test_settings_update(client, app):
    resp = client.post("/parametres/", data={
        "name": "Ma Super Agence", "city": "Agadir", "contract_prefix": "LOC", "engagement_prefix": "ENG",
        "currency": "MAD", "default_caution": "3000",
    }, follow_redirects=True)
    assert b"Ma Super Agence" in resp.data
    resp = client.post("/parametres/", data={"name": "X", "contract_prefix": "A", "engagement_prefix": "A"}, follow_redirects=True)
    assert "différents".encode() in resp.data


def test_template_crud(client, app):
    resp = client.post("/engagements/modeles/nouveau", data={
        "name": "Mon modèle", "title": "TITRE", "body": "Bonjour {{ client_nom }}", "active": "1",
    }, follow_redirects=True)
    assert b"Mon mod" in resp.data


def test_arabic_engagement(client, app, vehicle):
    from app.models import EngagementTemplate

    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        cnumber = Contract.query.one().number
        tpl = EngagementTemplate.query.filter_by(active=True).order_by(EngagementTemplate.name).first()
        assert tpl.title == "التزام بإرجاع السيارة"
        tpl_id, body = tpl.id, tpl.body
    page = client.get("/engagements/nouveau?contract_id=1")
    assert "التزام بإرجاع السيارة".encode() in page.data
    client.post("/engagements/nouveau", data={
        "template_id": str(tpl_id), "title": "التزام بإرجاع السيارة", "body_source": body,
        "client_name": "Alaoui Karim", "client_cin": "AB123456", "client_nationality": "Marocaine",
        "contract_number": cnumber, "doc_date": "2026-11-02",
    })
    with app.app_context():
        e = Engagement.query.one()
        assert "ALAOUI KARIM" in e.body and "مغربية" in e.body and "12345-A-6" in e.body
        eid = e.id
    view = client.get(f"/engagements/{eid}")
    assert b'dir="rtl"' in view.data and "توقيع المكتري".encode() in view.data
    pdf = client.get(f"/engagements/{eid}/pdf")
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")


def test_is_arabic():
    from app.utils import is_arabic

    assert is_arabic("أنا الموقع أسفله {{ client_nom }}")
    assert not is_arabic("Je soussigné {{ client_nom }}")
    assert not is_arabic("")


def test_logo_processing(tmp_path, app):
    from PIL import Image
    from app.logo import save_logo

    src = tmp_path / "in.jpg"
    img = Image.new("RGB", (400, 300), (235, 235, 230))
    img.paste((0, 0, 0), (100, 100, 200, 150))
    img.save(src)
    with app.app_context():
        out = save_logo(str(src), dest=str(tmp_path / "logo.png"))
    result = Image.open(out)
    assert result.width < 200 and result.height < 100  # recadré sur le contenu
    assert result.getpixel((1, 1)) == (255, 255, 255)  # fond blanchi


def test_invalid_logo_upload_rejected(client):
    import io

    resp = client.post("/parametres/", data={
        "name": "Agence", "contract_prefix": "CT", "engagement_prefix": "EG",
        "logo": (io.BytesIO(b"pas une image"), "logo.png"),
    }, content_type="multipart/form-data", follow_redirects=True)
    assert "pas une image valide".encode() in resp.data


def test_delete_contract_keeps_linked_documents(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        c = Contract.query.one()
        cid, cnumber = c.id, c.number
    client.get(f"/contrats/{cid}/dupliquer")
    client.post("/contrats/nouveau", data=contract_form(vehicle, start_at="2026-12-01T10:00", end_at="2026-12-03T10:00", source_id=str(cid)))
    client.post("/engagements/nouveau", data={"title": "T", "body_source": "x", "client_name": "X", "contract_number": cnumber})
    assert "Supprimer définitivement le contrat".encode() in client.get(f"/contrats/{cid}").data
    resp = client.post(f"/contrats/{cid}/supprimer", follow_redirects=True)
    assert "supprimé définitivement".encode() in resp.data
    with app.app_context():
        assert db.session.get(Contract, cid) is None
        copy = Contract.query.one()
        assert copy.source_id is None
        e = Engagement.query.one()
        assert e.contract_id is None and e.contract_number == cnumber


def test_delete_client_and_vehicle_keep_history(client, app, vehicle):
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    with app.app_context():
        c = Contract.query.one()
        cid, client_id = c.id, c.client_id
    resp = client.post(f"/clients/{client_id}/supprimer", follow_redirects=True)
    assert "restent dans l".encode() in resp.data
    resp = client.post(f"/vehicules/{vehicle}/supprimer", follow_redirects=True)
    assert "supprimé".encode() in resp.data
    with app.app_context():
        assert Client.query.count() == 0 and Vehicle.query.count() == 0
        c = db.session.get(Contract, cid)
        assert c.client_id is None and c.vehicle_id is None
        assert c.client_name == "ALAOUI Karim" and c.vehicle_plate == "12345-A-6"
    # les pages restent consultables sans fiche client ni véhicule
    for url in ["/", "/contrats/", f"/contrats/{cid}", f"/contrats/{cid}/pdf", f"/contrats/{cid}/dupliquer", f"/contrats/{cid}/modifier"]:
        assert client.get(url).status_code == 200, url
    for url in ["/clients/", "/vehicules/"]:
        assert client.get(url).status_code == 200


def test_logo_upload_route_and_removal(client, app, tmp_path):
    import io
    from PIL import Image

    app.instance_path = str(tmp_path)  # n'écrit pas dans le vrai dossier instance
    default_size = len(client.get("/logo.png").data)  # logo par défaut livré
    buf = io.BytesIO()
    img = Image.new("RGB", (300, 200), "white")
    img.paste((0, 0, 0), (50, 50, 250, 150))
    img.save(buf, "PNG")
    buf.seek(0)
    base = {"name": "Agence", "contract_prefix": "CT", "engagement_prefix": "EG"}
    client.post("/parametres/", data={**base, "logo": (buf, "logo.png")}, content_type="multipart/form-data")
    assert (tmp_path / "logo.png").is_file()
    uploaded = client.get("/logo.png")
    assert uploaded.status_code == 200 and len(uploaded.data) != default_size
    client.post("/parametres/", data={**base, "remove_logo": "1"}, content_type="multipart/form-data")
    assert client.get("/logo.png").status_code == 404


# ---------------------------------------------------------------- interface bilingue

def test_all_texts_translated_to_arabic(app):
    import re
    from app.i18n_keys import all_keys
    from app.translations_ar import AR

    with app.app_context():
        keys = all_keys()
    missing = sorted(k for k in keys if k not in AR)
    assert not missing, f"Textes sans traduction arabe : {missing}"
    for key in keys:
        assert set(re.findall(r"\{(\w+)\}", key)) == set(re.findall(r"\{(\w+)\}", AR[key])), key


ALL_PAGES = ["/", "/clients/", "/clients/nouveau", "/vehicules/", "/vehicules/nouveau",
             "/contrats/", "/contrats/nouveau", "/engagements/", "/engagements/nouveau",
             "/engagements/modeles", "/engagements/modeles/nouveau", "/parametres/"]


def test_arabic_interface(client, app, vehicle):
    client.set_cookie("lang", "ar")
    client.post("/contrats/nouveau", data=contract_form(vehicle))
    pages = ALL_PAGES + ["/contrats/1", "/contrats/1/modifier", "/contrats/1/dupliquer",
                         "/clients/1", "/clients/1/modifier", f"/vehicules/{vehicle}", f"/vehicules/{vehicle}/modifier"]
    for url in pages:
        resp = client.get(url)
        assert resp.status_code == 200, url
        assert b'dir="rtl"' in resp.data and b"bootstrap.rtl.min.css" in resp.data, url
    assert "لوحة القيادة".encode() in client.get("/").data
    assert "عقد جديد".encode() in client.get("/contrats/").data
    # les messages du serveur sont aussi traduits
    resp = client.post("/contrats/nouveau", data=contract_form(vehicle, end_at="2026-11-01T10:00"), follow_redirects=True)
    assert "يجب أن يكون تاريخ العودة بعد تاريخ المغادرة".encode() in resp.data
    # la feuille du contrat reste bilingue et de gauche à droite
    assert b'id="document" dir="ltr"' in client.get("/contrats/1").data


def test_language_switch(client):
    resp = client.get("/langue/fr", headers={"Referer": "http://localhost/clients/"})
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/clients/")
    assert "lang=fr" in resp.headers["Set-Cookie"]
    page = client.get("/")
    assert b'dir="ltr"' in page.data and b"Tableau de bord" in page.data
    client.get("/langue/ar")
    assert b'dir="rtl"' in client.get("/").data
    # code inconnu ou redirection externe : ignorés
    resp = client.get("/langue/xx", headers={"Referer": "https://exemple.com/"})
    assert resp.headers["Location"].endswith("/") and "exemple.com" not in resp.headers["Location"]


def test_default_language_is_arabic():
    from app import create_app
    from app.config import TestConfig

    class ArabicConfig(TestConfig):
        DEFAULT_LANGUAGE = "ar"

    app = create_app(ArabicConfig)
    assert b'dir="rtl"' in app.test_client().get("/").data
