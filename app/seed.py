"""Création des tables et données initiales (paramètres agence, modèles d'engagement)."""
from .extensions import db
from .models import Agency, EngagementTemplate

DEFAULT_TERMS = (
    "J'ai lu et j'accepte les termes mentionnés au recto et au verso du présent contrat "
    "et du carnet de bord. La société {agence} se réserve le plein droit de récupérer "
    "la voiture à tout moment sans justificatif ni indemnité."
)

DEFAULT_TERMS_AR = (
    "لقد قرأت جميع البنود المدونة خلف هذا العقد و قبلت بها و أتحمل مسؤولية السيارة "
    "خلال مدة هذا العقد. {agence} لها كامل الصلاحية في استرجاع سيارتها في أي وقت "
    "وذلك دون تعويض و يعتبر هذا العقد لاغيا في حالة انتهاء التاريخ المدون أعلاه."
)

DEFAULT_TEMPLATES = [
    {
        "name": "إرجاع السيارة — Restitution du véhicule",
        "title": "التزام بإرجاع السيارة",
        "body": (
            "أنا الموقع(ة) أسفله السيد(ة) {{ client_nom }}، الجنسية: {{ client_nationalite }}، "
            "الحامل(ة) للبطاقة الوطنية رقم {{ client_cin }} / جواز السفر رقم {{ client_passeport }}، "
            "ورخصة السياقة رقم {{ client_permis }}، الساكن(ة) ب {{ client_adresse }}، "
            "الهاتف: {{ client_telephone }}،\n\n"
            "ألتزم بإرجاع السيارة من نوع {{ vehicule }} ذات رقم التسجيل {{ immatriculation }}، "
            "المكتراة من وكالة {{ agence_nom }} بموجب العقد رقم {{ contrat_numero }}، "
            "في أجل أقصاه {{ date_fin }}، في نفس الحالة التي تسلمتها بها، مع جميع وثائقها ولوازمها.\n\n"
            "وفي حالة التأخير دون إذن من الوكالة، أقبل أداء ثمن كل يوم إضافي حسب التعريفة "
            "المعمول بها، وأخول للوكالة الحق في اتخاذ جميع الإجراءات القانونية لاسترجاع السيارة."
        ),
    },
    {
        "name": "تحمل المسؤولية — Responsabilité amendes et infractions",
        "title": "التزام بتحمل المسؤولية",
        "body": (
            "أنا الموقع(ة) أسفله السيد(ة) {{ client_nom }}، الحامل(ة) للبطاقة الوطنية رقم "
            "{{ client_cin }} ورخصة السياقة رقم {{ client_permis }}،\n\n"
            "أقر بأنني تسلمت السيارة من نوع {{ vehicule }} ذات رقم التسجيل {{ immatriculation }} "
            "خلال الفترة الممتدة من {{ date_debut }} إلى {{ date_fin }}.\n\n"
            "وألتزم بتحمل كامل المسؤولية المدنية والجنائية عن جميع المخالفات المرورية والغرامات "
            "والأضرار التي قد تقع خلال هذه الفترة، وبأداء مبالغها عند أول طلب من وكالة {{ agence_nom }}."
        ),
    },
    {
        "name": "إيداع الضمانة — Reconnaissance de caution",
        "title": "إقرار بإيداع الضمانة",
        "body": (
            "أنا الموقع(ة) أسفله السيد(ة) {{ client_nom }}، الحامل(ة) للبطاقة الوطنية رقم {{ client_cin }}،\n\n"
            "أصرح بأنني سلمت لوكالة {{ agence_nom }} مبلغ ضمانة قدره {{ montant }} كضمان لكراء "
            "السيارة من نوع {{ vehicule }} ذات رقم التسجيل {{ immatriculation }} "
            "(العقد رقم {{ contrat_numero }}).\n\n"
            "وتسترجع هذه الضمانة عند إرجاع السيارة، بعد خصم ما قد يترتب من أضرار أو نقص في "
            "الوقود أو أيام إضافية أو غرامات."
        ),
    },
]

# Anciens modèles français (première version) : désactivés s'ils n'ont pas été modifiés
FRENCH_TEMPLATES = [
    {
        "name": "Restitution du véhicule",
        "title": "ENGAGEMENT DE RESTITUTION DU VÉHICULE",
        "body": (
            "Je soussigné(e) {{ client_nom }}, de nationalité {{ client_nationalite }}, "
            "titulaire de la CIN N° {{ client_cin }} / passeport N° {{ client_passeport }}, "
            "permis de conduire N° {{ client_permis }}, demeurant à {{ client_adresse }}, "
            "téléphone {{ client_telephone }},\n\n"
            "m'engage à restituer à l'agence {{ agence_nom }} le véhicule {{ vehicule }} "
            "immatriculé {{ immatriculation }}, loué dans le cadre du contrat N° {{ contrat_numero }}, "
            "au plus tard le {{ date_fin }}, dans l'état où il m'a été remis, avec l'ensemble "
            "de ses papiers et accessoires.\n\n"
            "En cas de retard non autorisé, j'accepte que l'agence facture chaque journée "
            "supplémentaire au tarif en vigueur et engage toute procédure utile pour récupérer "
            "le véhicule."
        ),
    },
    {
        "name": "Responsabilité amendes et infractions",
        "title": "ENGAGEMENT DE RESPONSABILITÉ",
        "body": (
            "Je soussigné(e) {{ client_nom }}, titulaire de la CIN N° {{ client_cin }} "
            "et du permis de conduire N° {{ client_permis }},\n\n"
            "reconnais avoir pris en charge le véhicule {{ vehicule }} immatriculé "
            "{{ immatriculation }} du {{ date_debut }} au {{ date_fin }}.\n\n"
            "Je m'engage à assumer l'entière responsabilité civile et pénale de toutes les "
            "infractions au code de la route, amendes, contraventions et dommages survenus "
            "pendant cette période, et à en régler le montant à première demande de l'agence "
            "{{ agence_nom }}."
        ),
    },
    {
        "name": "Reconnaissance de caution",
        "title": "RECONNAISSANCE DE DÉPÔT DE CAUTION",
        "body": (
            "Je soussigné(e) {{ client_nom }}, titulaire de la CIN N° {{ client_cin }}, "
            "déclare avoir remis à l'agence {{ agence_nom }} une caution d'un montant de "
            "{{ montant }} en garantie de la location du véhicule {{ vehicule }} "
            "immatriculé {{ immatriculation }} (contrat N° {{ contrat_numero }}).\n\n"
            "Cette caution me sera restituée lors du retour du véhicule, déduction faite "
            "des éventuels dommages, franchises, carburant manquant, jours supplémentaires "
            "ou amendes constatés."
        ),
    },
]


def init_db():
    db.create_all()
    if Agency.query.first() is None:
        db.session.add(
            Agency(
                name="APOLLO CAR",
                name_ar="كراء السيارات",
                slogan="Location de voitures",
                address="Lot 707 AV Amar bn Aasser 94 Hay El Quods",
                city="Laâyoune",
                phone="06 98 01 98 17 - 06 00 75 87 34",
                contract_terms=DEFAULT_TERMS.replace("{agence}", "APOLLO CAR"),
                contract_terms_ar=DEFAULT_TERMS_AR.replace("{agence}", "APOLLO CAR"),
                default_caution=5000,
            )
        )
    existing = {t.name for t in EngagementTemplate.query.all()}
    for tpl in DEFAULT_TEMPLATES:
        if tpl["name"] not in existing:
            db.session.add(EngagementTemplate(**tpl))
    for tpl in FRENCH_TEMPLATES:
        EngagementTemplate.query.filter_by(name=tpl["name"], body=tpl["body"], active=True).update(
            {"active": False}
        )
    db.session.commit()
