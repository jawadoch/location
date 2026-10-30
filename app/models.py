from datetime import datetime, date

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class Agency(TimestampMixin, db.Model):
    """Paramètres de l'agence (une seule ligne)."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="Mon Agence")
    name_ar = db.Column(db.String(120), default="")
    slogan = db.Column(db.String(160), default="Location de voitures")
    address = db.Column(db.String(255), default="")
    city = db.Column(db.String(80), default="")
    phone = db.Column(db.String(80), default="")
    email = db.Column(db.String(120), default="")
    website = db.Column(db.String(120), default="")
    ice = db.Column(db.String(40), default="")
    rc = db.Column(db.String(40), default="")
    tax_id = db.Column(db.String(40), default="")  # Identifiant fiscal (IF)
    patente = db.Column(db.String(40), default="")
    contract_prefix = db.Column(db.String(10), default="CT")
    engagement_prefix = db.Column(db.String(10), default="EG")
    default_caution = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default="DH")
    contract_terms = db.Column(db.Text, default="")
    contract_terms_ar = db.Column(db.Text, default="")

    @classmethod
    def get(cls):
        agency = cls.query.first()
        if agency is None:
            agency = cls()
            db.session.add(agency)
            db.session.commit()
        return agency


class Client(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(80), default="")
    nationality = db.Column(db.String(60), default="Marocaine")
    birth_date = db.Column(db.Date)
    cin = db.Column(db.String(30), index=True)
    cin_valid_until = db.Column(db.Date)
    passport_no = db.Column(db.String(30), index=True)
    passport_issued_at = db.Column(db.String(80), default="")
    license_no = db.Column(db.String(40))
    license_date = db.Column(db.Date)
    license_place = db.Column(db.String(80), default="")
    address = db.Column(db.String(255), default="")
    city = db.Column(db.String(80), default="")
    phone = db.Column(db.String(40), index=True)
    email = db.Column(db.String(120), default="")
    notes = db.Column(db.Text, default="")

    contracts = db.relationship("Contract", back_populates="client", lazy="dynamic")
    engagements = db.relationship("Engagement", back_populates="client", lazy="dynamic")

    @property
    def full_name(self):
        return " ".join(p for p in [self.last_name, self.first_name] if p).strip()

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "last_name": self.last_name,
            "first_name": self.first_name or "",
            "nationality": self.nationality or "",
            "birth_date": self.birth_date.isoformat() if self.birth_date else "",
            "cin": self.cin or "",
            "passport_no": self.passport_no or "",
            "passport_issued_at": self.passport_issued_at or "",
            "license_no": self.license_no or "",
            "license_date": self.license_date.isoformat() if self.license_date else "",
            "license_place": self.license_place or "",
            "address": self.address or "",
            "city": self.city or "",
            "phone": self.phone or "",
            "email": self.email or "",
        }


VEHICLE_STATUSES = {
    "disponible": "Disponible",
    "maintenance": "En maintenance",
    "hors_service": "Hors service",
}

FUEL_TYPES = ["Diesel", "Essence", "Hybride", "Électrique"]


class Vehicle(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    plate = db.Column(db.String(30), unique=True, nullable=False)
    year = db.Column(db.Integer)
    color = db.Column(db.String(30), default="")
    fuel = db.Column(db.String(20), default="Diesel")
    gearbox = db.Column(db.String(20), default="Manuelle")
    mileage = db.Column(db.Integer, default=0)
    daily_rate = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(20), default="disponible", nullable=False)
    insurance_expiry = db.Column(db.Date)
    technical_visit_expiry = db.Column(db.Date)
    notes = db.Column(db.Text, default="")

    contracts = db.relationship("Contract", back_populates="vehicle", lazy="dynamic")

    @property
    def label(self):
        return f"{self.brand} {self.model}"

    @property
    def status_label(self):
        return VEHICLE_STATUSES.get(self.status, self.status)

    def active_contract(self, at=None):
        at = at or datetime.now()
        return (
            self.contracts.filter(
                Contract.status == "en_cours",
                Contract.start_at <= at,
                Contract.end_at >= at,
            )
            .order_by(Contract.start_at.desc())
            .first()
        )

    @property
    def is_rented(self):
        return self.active_contract() is not None


CONTRACT_STATUSES = {
    "en_cours": "En cours",
    "termine": "Terminé",
    "annule": "Annulé",
}

DOCUMENT_FLAGS = [
    ("doc_carte_grise", "Carte grise", "البطاقة الرمادية"),
    ("doc_assurance", "Assurance", "التأمين"),
    ("doc_vignette", "Vignette", "الضريبة"),
    ("doc_visite", "Visite technique", "الفحص التقني"),
    ("doc_autorisation", "Autorisation", "الترخيص"),
    ("doc_contrat", "Contrat", "العقد"),
]

FUEL_LEVELS = ["Vide", "1/4", "1/2", "3/4", "Plein"]
PAYMENT_METHODS = ["Espèces", "Carte bancaire", "Virement", "Chèque"]


class Contract(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default="en_cours", nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey("contract.id"))

    client_id = db.Column(db.Integer, db.ForeignKey("client.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))

    # Instantané du client au moment du contrat
    client_name = db.Column(db.String(160), nullable=False, index=True)
    client_last_name = db.Column(db.String(80), default="")
    client_first_name = db.Column(db.String(80), default="")
    client_nationality = db.Column(db.String(60), default="")
    client_birth_date = db.Column(db.Date)
    client_cin = db.Column(db.String(30), default="", index=True)
    client_passport = db.Column(db.String(30), default="")
    client_passport_issued_at = db.Column(db.String(80), default="")
    client_license_no = db.Column(db.String(40), default="")
    client_license_date = db.Column(db.Date)
    client_license_place = db.Column(db.String(80), default="")
    client_address = db.Column(db.String(255), default="")
    client_phone = db.Column(db.String(40), default="", index=True)

    # Second conducteur
    driver2_name = db.Column(db.String(160), default="")
    driver2_license_no = db.Column(db.String(40), default="")
    driver2_license_date = db.Column(db.Date)
    driver2_license_place = db.Column(db.String(80), default="")
    driver2_cin = db.Column(db.String(30), default="")
    driver2_cin_date = db.Column(db.Date)

    # Instantané du véhicule
    vehicle_brand = db.Column(db.String(60), default="")
    vehicle_model = db.Column(db.String(60), default="")
    vehicle_plate = db.Column(db.String(30), default="", index=True)

    # Location
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    prolongation = db.Column(db.String(120), default="")
    pickup_place = db.Column(db.String(120), default="")
    return_place = db.Column(db.String(120), default="")
    km_start = db.Column(db.Integer)
    km_end = db.Column(db.Integer)
    fuel_level = db.Column(db.String(10), default="Plein")
    washing = db.Column(db.Boolean, default=False)
    accessories = db.Column(db.String(255), default="")

    doc_carte_grise = db.Column(db.Boolean, default=True)
    doc_assurance = db.Column(db.Boolean, default=True)
    doc_vignette = db.Column(db.Boolean, default=True)
    doc_visite = db.Column(db.Boolean, default=True)
    doc_autorisation = db.Column(db.Boolean, default=False)
    doc_contrat = db.Column(db.Boolean, default=True)

    # Véhicule changé
    changed_brand = db.Column(db.String(80), default="")
    changed_plate = db.Column(db.String(30), default="")
    changed_date = db.Column(db.Date)

    # Montants
    daily_rate = db.Column(db.Float, default=0, nullable=False)
    days = db.Column(db.Integer, default=1, nullable=False)
    amount = db.Column(db.Float, default=0, nullable=False)
    advance = db.Column(db.Float, default=0, nullable=False)
    caution = db.Column(db.Float, default=0, nullable=False)
    payment_method = db.Column(db.String(30), default="Espèces")
    notes = db.Column(db.Text, default="")

    client = db.relationship("Client", back_populates="contracts")
    vehicle = db.relationship("Vehicle", back_populates="contracts")
    source = db.relationship("Contract", remote_side=[id], backref="copies")

    @property
    def remaining(self):
        return round((self.amount or 0) - (self.advance or 0), 2)

    @property
    def vehicle_label(self):
        return f"{self.vehicle_brand} {self.vehicle_model}".strip()

    @property
    def status_label(self):
        return CONTRACT_STATUSES.get(self.status, self.status)

    @property
    def km_driven(self):
        if self.km_start is not None and self.km_end is not None:
            return self.km_end - self.km_start
        return None


class EngagementTemplate(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

    engagements = db.relationship("Engagement", back_populates="template", lazy="dynamic")


class Engagement(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    source_id = db.Column(db.Integer, db.ForeignKey("engagement.id"))
    template_id = db.Column(db.Integer, db.ForeignKey("engagement_template.id"))
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))
    contract_id = db.Column(db.Integer, db.ForeignKey("contract.id"))

    title = db.Column(db.String(160), nullable=False)
    body_source = db.Column(db.Text, nullable=False)  # texte avec variables {{ ... }}
    body = db.Column(db.Text, nullable=False)  # texte final figé
    doc_date = db.Column(db.Date, default=date.today, nullable=False)
    place = db.Column(db.String(80), default="")
    amount = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    # Instantanés
    client_name = db.Column(db.String(160), nullable=False, index=True)
    client_cin = db.Column(db.String(30), default="", index=True)
    client_passport = db.Column(db.String(30), default="")
    client_license_no = db.Column(db.String(40), default="")
    client_address = db.Column(db.String(255), default="")
    client_phone = db.Column(db.String(40), default="")
    client_nationality = db.Column(db.String(60), default="")
    vehicle_label = db.Column(db.String(120), default="")
    vehicle_plate = db.Column(db.String(30), default="")
    contract_number = db.Column(db.String(30), default="")

    template = db.relationship("EngagementTemplate", back_populates="engagements")
    client = db.relationship("Client", back_populates="engagements")
    vehicle = db.relationship("Vehicle")
    contract = db.relationship("Contract")
    source = db.relationship("Engagement", remote_side=[id], backref="copies")


class GeneralConditions(TimestampMixin, db.Model):
    """Conditions générales de location (verso du contrat), texte bilingue modifiable."""

    id = db.Column(db.Integer, primary_key=True)
    title_fr = db.Column(db.String(160), nullable=False)
    title_ar = db.Column(db.String(160), nullable=False)
    body_fr = db.Column(db.Text, nullable=False)
    body_ar = db.Column(db.Text, nullable=False)

    @classmethod
    def get(cls):
        conditions = cls.query.first()
        if conditions is None:
            from .conditions import default_conditions

            conditions = cls(**default_conditions(Agency.get().city))
            db.session.add(conditions)
            db.session.commit()
        return conditions
