"""Conditions générales de location (verso du contrat) : textes par défaut et mise en forme.

Syntaxe du texte (une ligne = un élément) :
    ## Titre de section
    [x] Ligne avec une case cochée
    - Ligne avec une puce
    Toute autre ligne = paragraphe.
"""

CITIES_AR = {
    "laâyoune": "العيون", "laayoune": "العيون", "dakhla": "الداخلة", "casablanca": "الدار البيضاء",
    "rabat": "الرباط", "marrakech": "مراكش", "agadir": "أكادير", "tanger": "طنجة", "fès": "فاس",
    "fes": "فاس", "meknès": "مكناس", "oujda": "وجدة", "tétouan": "تطوان", "guelmim": "كلميم",
}

DEFAULT_FR = """## ÂGE LÉGAL POUR LOUER
[x] L'âge minimum est de 20 ans et l'âge maximum de 70 ans.
[x] Les conducteurs n'ayant pas l'âge mentionné ci-dessus ne sont pas autorisés.

## LOCATAIRE ET CHAUFFEUR SUPPLÉMENTAIRE
Les deux conducteurs doivent être présents lors de l'établissement du contrat de location. Leur permis de conduire doit avoir plus de deux ans et être valide pour une période d'au moins un an.
Le conducteur supplémentaire a les mêmes responsabilités que le conducteur officiel. La société autorise un conducteur supplémentaire gratuitement.

## DURÉE DE LOCATION
La durée de location minimale est de 48 heures. Tout dépassement de plus de trois heures est facturé comme un jour supplémentaire.

## CAUTION ET PROLONGATION
La caution déposée par le locataire ne pourra en aucun cas servir à une prolongation. Le locataire doit demander la prolongation de la location au moins 48 heures à l'avance, en l'accompagnant de la provision correspondante, sous peine de s'exposer à des poursuites judiciaires pour détournement de véhicule et abus de confiance. Le loueur se réserve le droit de refuser la prolongation et de récupérer immédiatement le véhicule.

## ASSURANCE AUTO
L'assurance couvre les dommages illimités conformément à la réglementation en vigueur au Maroc.
En cas d'accident ou de dommage, vous devez présenter immédiatement un rapport de police. À défaut de rapport de police valide, le locataire paie tous les frais engagés, même si la collision est incluse dans la souscription d'assurance. Aucune voiture de remplacement ne sera proposée et la location sera facturée jusqu'à la réception du rapport de police et des documents.
Si la voiture est immobilisée pour réparation, le locataire paie le loyer quotidien jusqu'à la fin de la réparation.
En cas de vol de la voiture de location, la police doit en être immédiatement informée, sinon la couverture peut être nulle.

## AMENDES ET CONTRAVENTIONS
Le locataire et les conducteurs agréés sont responsables des amendes, contraventions et procès-verbaux établis à leur encontre. Le locataire s'engage à rembourser à la société tout montant qu'elle aurait été amenée à avancer.

## PAIEMENTS
Le montant de la location est payé en espèces, directement à la livraison de la voiture objet du contrat de location.

## DÉPÔT DE GARANTIE
Un dépôt est exigé pour couvrir tous les frais en cas de dommage ou de vol. Quel que soit le mode de paiement utilisé, vous devez laisser un montant déterminé selon la voiture louée. Ce dépôt doit être effectué en espèces.

## KILOMÉTRAGE
Le kilométrage maximum est de 200 km par jour. Au-delà de 200 km par jour, chaque kilomètre supplémentaire est facturé 0,6 DH TTC.

## JURIDICTION
En cas de litige pouvant naître de l'exécution du présent contrat, les tribunaux de {ville} sont seuls compétents."""

DEFAULT_AR = """## السن القانوني للكراء
[x] الحد الأدنى للسن هو 20 سنة والحد الأقصى هو 70 سنة.
[x] لا يسمح بالسياقة للسائقين الذين يقل سنهم أو يفوق السن المذكور أعلاه.

## المكتري والسائق الإضافي
يجب أن يكون السائقان حاضرين عند إبرام عقد الكراء، وأن تكون رخصة السياقة لكل منهما قد مر على تسليمها أكثر من سنتين وصالحة لمدة سنة على الأقل.
يتحمل السائق الإضافي نفس مسؤوليات السائق الرسمي، وتسمح الشركة بسائق إضافي مجانا.

## مدة الكراء
الحد الأدنى لمدة الكراء هو 48 ساعة، وكل تجاوز لأكثر من ثلاث ساعات يحتسب يوما إضافيا.

## الضمانة والتمديد
لا يمكن بأي حال من الأحوال استعمال الضمانة المودعة من طرف المكتري لتمديد الكراء. ويجب على المكتري طلب تمديد الكراء قبل 48 ساعة على الأقل مع أداء المبلغ المقابل، وإلا تعرض للمتابعة القضائية من أجل اختلاس السيارة وخيانة الأمانة. ويحتفظ المكري بحق رفض التمديد واسترجاع السيارة فورا.

## التأمين على السيارة
يغطي التأمين الأضرار غير المحدودة وفقا للقوانين الجاري بها العمل بالمغرب.
في حالة وقوع حادثة أو ضرر، يجب الإدلاء فورا بمحضر الشرطة. وفي حالة عدم الإدلاء بمحضر صالح، يتحمل المكتري جميع المصاريف، حتى ولو كان الاصطدام مشمولا بعقد التأمين. ولا تقترح أي سيارة بديلة، ويستمر احتساب ثمن الكراء إلى حين التوصل بمحضر الشرطة والوثائق.
إذا كانت السيارة متوقفة من أجل الإصلاح، يؤدي المكتري ثمن الكراء اليومي إلى حين انتهاء الإصلاح.
في حالة سرقة السيارة المكتراة، يجب إخبار الشرطة فورا، وإلا قد تصبح التغطية لاغية.

## الغرامات والمخالفات
يتحمل المكتري والسائقون المرخص لهم مسؤولية الغرامات والمخالفات والمحاضر المحررة في حقهم، ويلتزم المكتري بإرجاع كل مبلغ قد تضطر الشركة إلى تسبيقه.

## الأداء
يؤدى مبلغ الكراء نقدا مباشرة عند تسليم السيارة موضوع عقد الكراء.

## الضمانة المالية
تطلب ضمانة مالية لتغطية جميع المصاريف في حالة الضرر أو السرقة. ومهما كانت طريقة الأداء، يجب ترك مبلغ يحدد حسب السيارة المكتراة، ويودع هذا المبلغ نقدا.

## عدد الكيلومترات
الحد الأقصى هو 200 كلم في اليوم. وفي حالة تجاوز 200 كلم في اليوم، يحتسب كل كيلومتر إضافي ب 0,6 درهم مع احتساب الرسوم.

## الاختصاص القضائي
في حالة نزاع ناتج عن تنفيذ هذا العقد، تكون محاكم {ville} هي المختصة."""


def default_conditions(city=""):
    city = (city or "").strip()
    city_ar = CITIES_AR.get(city.lower(), city) or "........"
    return {
        "title_fr": "Conditions générales de location",
        "title_ar": "الشروط العامة للكراء",
        "body_fr": DEFAULT_FR.replace("{ville}", city or "........"),
        "body_ar": DEFAULT_AR.replace("{ville}", city_ar),
    }


def parse_blocks(text):
    """Découpe le texte en éléments : ("title" | "check" | "bullet" | "para", texte)."""
    blocks = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            blocks.append(("title", line.lstrip("#").strip()))
        elif line[:3].lower() == "[x]":
            blocks.append(("check", line[3:].strip()))
        elif line.startswith(("- ", "• ")):
            blocks.append(("bullet", line[2:].strip()))
        else:
            blocks.append(("para", line))
    return blocks
