# Gestion d'agence de location de voitures

Application web Flask pour une agence de location de voitures au Maroc : clients, véhicules,
contrats de location (impression A4 et PDF bilingue français / arabe), engagements à partir de
modèles, recherche et duplication de documents, tableau de bord.

**Technologies :** Python 3.10+, Flask, SQLAlchemy (SQLite), Bootstrap 5 (fourni en local,
fonctionne sans Internet), xhtml2pdf pour les PDF (100 % Python, aucun logiciel à installer
sous Windows).

---

## Langue de l'interface : arabe et français

L'interface s'ouvre **en arabe** (de droite à gauche). Les boutons **عربي / Français** en haut
de chaque page permettent de changer de langue ; le choix est mémorisé sur le PC.

- Les contrats imprimés restent **bilingues** (français + arabe), comme le modèle papier.
- Les engagements sont rédigés en arabe (modèles fournis) ; un modèle écrit en français
  produit un engagement en français.
- Pour démarrer en français par défaut : variable d'environnement `LANGUE=fr`.
- Les traductions sont dans `app/translations_ar.py` (clé = texte français). Le test
  `test_all_texts_translated_to_arabic` échoue si un texte de l'interface n'a pas de traduction.

---

## Installation chez le client (sans aucune commande)

L'utilisateur final n'a jamais besoin de taper de commande : il double-clique sur l'icône
**Apollo Car** du Bureau, l'application démarre en arrière-plan (sans fenêtre noire) et le
navigateur s'ouvre directement sur `http://127.0.0.1:5000`.

### Étapes (à faire une seule fois sur le PC du client)

1. **Récupérer le projet** : sur https://github.com/jawadoch/location, bouton **Code →
   Download ZIP**, puis extraire le ZIP dans un dossier fixe, par exemple `C:\ApolloCar`
   (évitez le Bureau ou Téléchargements, l'application doit rester à cet endroit).
   Avec Git : `git clone https://github.com/jawadoch/location.git C:\ApolloCar`
2. **Double-cliquer sur `INSTALLER.bat`** dans ce dossier. Le script :
   - vérifie Python 3.10+ (et l'installe automatiquement via `winget` s'il manque ;
     sinon il indique de l'installer depuis https://www.python.org/downloads/ en cochant
     **« Add python.exe to PATH »**) ;
   - crée l'environnement `.venv` et installe les composants (connexion Internet nécessaire,
     quelques minutes) ;
   - crée la base de données ;
   - crée les raccourcis **« Apollo Car »** et **« Apollo Car - Arreter »** sur le Bureau,
     et « Apollo Car » dans le menu Démarrer ;
   - ouvre l'application.
3. **Vérifier** les informations de l'agence et le logo dans **Paramètres**.

### Utilisation au quotidien

| Action | Comment |
|---|---|
| Ouvrir l'application | Double-clic sur **Apollo Car** (Bureau ou menu Démarrer). Si elle tourne déjà, le navigateur s'ouvre simplement. |
| Fermer | Fermer l'onglet du navigateur suffit. L'application reste prête en arrière-plan et s'arrête à l'extinction du PC. |
| Arrêter complètement | Double-clic sur **Apollo Car - Arreter**. |
| En cas de problème | Le journal est dans `instance\app.log`. |

> Ne rien installer sur un compte et utiliser un autre : les raccourcis sont créés pour la
> session Windows qui exécute `INSTALLER.bat`.

### Mise à jour de l'application chez le client

Remplacer les fichiers du dossier par la nouvelle version **en conservant le dossier
`instance`** (il contient la base `location.db` et le logo envoyé depuis Paramètres), puis
double-cliquer à nouveau sur `INSTALLER.bat`.
Avec Git : `git pull` puis `INSTALLER.bat`.

---

## Installation pour le développement (PowerShell)

Ouvrez PowerShell dans le dossier du projet, puis :

```powershell
# 1. Créer l'environnement virtuel (Python 3.10 ou plus récent)
py -3 -m venv .venv

# 2. Installer les dépendances
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Lancer l'application
.\.venv\Scripts\python.exe run.py
```

Ouvrez ensuite **http://127.0.0.1:5000** dans votre navigateur.

La base de données `instance\location.db` est créée automatiquement au premier lancement,
avec les paramètres de l'agence et trois modèles d'engagement par défaut.

> Si vous préférez activer l'environnement (`.\.venv\Scripts\Activate.ps1`) et que PowerShell
> le refuse, exécutez une fois :
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
> Vous pourrez alors utiliser simplement `python run.py`.

### Options de lancement

```powershell
# Rendre l'application accessible aux autres postes du réseau local, sur le port 8080
$env:HOST = "0.0.0.0"; $env:PORT = "8080"; .\.venv\Scripts\python.exe run.py

# Clé secrète personnalisée (recommandé en production)
$env:SECRET_KEY = "une-longue-chaine-aleatoire"; .\.venv\Scripts\python.exe run.py

# Mode développement (rechargement automatique)
$env:FLASK_DEBUG = "1"; .\.venv\Scripts\python.exe run.py
```

### Lancer les tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

---

## Fonctionnalités

| Module | Ce que vous pouvez faire |
|---|---|
| **Tableau de bord** | Contrats en cours, véhicules disponibles / loués, CA du mois, reste à encaisser, retours prévus et retards, assurances et visites techniques à renouveler. |
| **Clients** | Ajouter, modifier, rechercher (nom, CIN, passeport, téléphone), voir l'historique des contrats et engagements. Doublons CIN / passeport refusés. |
| **Véhicules** | Ajouter, modifier, consulter ; tarif journalier, kilométrage, statut (disponible, maintenance, hors service), échéances assurance / visite technique, historique des locations. |
| **Contrats** | Création avec recherche d'un client existant (préremplissage automatique), calcul automatique des jours et du montant, avance, reste, caution, papiers remis, second conducteur, véhicule changé, clôture au retour (kilométrage, carburant), annulation. |
| **Engagements** | Rédigés **en arabe** pour être bien compris par le locataire (3 modèles fournis : إرجاع السيارة، تحمل المسؤولية، إيداع الضمانة). Document de droite à gauche avec tableau « بيانات المكتري والسيارة », libellés et zones de signature en arabe. Modèles personnalisables (variables `{{ client_nom }}`, `{{ immatriculation }}`…), liaison à un contrat, impression et PDF. Un modèle écrit en français produit un document en français. |
| **Recherche / duplication** | Recherche des contrats et engagements par nom, CIN, passeport, téléphone, numéro de document ou immatriculation. Bouton **Dupliquer** : formulaire prérempli, nouveau numéro, l'original reste intact et la copie garde un lien vers lui. |
| **Paramètres** | Logo (affiché sur les contrats et engagements ; recadré et fond blanchi automatiquement à l'envoi), nom (FR / AR), adresse, téléphones, ICE, RC, IF, patente, préfixes de numérotation, devise, caution par défaut, conditions imprimées en français et en arabe. |

### Numérotation

Chaque document reçoit un numéro unique `PREFIXE-ANNÉE-NNNN` (ex. `CT-2026-0001`,
`EG-2026-0001`). Les préfixes se modifient dans **Paramètres**.

### Historique et instantanés

Chaque contrat enregistre une **copie des informations du client et du véhicule** au moment de sa
création. Modifier ensuite une fiche client ou véhicule ne change pas les contrats déjà établis.
Les engagements conservent de la même façon le texte final figé.

Lors d'un contrat, si aucun client existant n'est sélectionné, l'application retrouve la fiche par
CIN ou passeport, ou en crée une automatiquement. La fiche est complétée avec les dernières
informations saisies.

### Impression et PDF

- **Imprimer (A4)** : la page du document utilise une feuille de style d'impression dédiée
  (`app/static/css/print.css`) qui n'imprime que la feuille A4. Dans la boîte d'impression,
  choisissez le format A4, des marges « Aucune » ou « Par défaut » et cochez « Graphiques
  d'arrière-plan » si besoin.
- **Télécharger le PDF** : PDF généré côté serveur par xhtml2pdf.
- **Arabe dans les PDF** : l'application utilise automatiquement la police Arial de Windows
  (`C:\Windows\Fonts\arial.ttf`). Pour une autre police (par ex. *Amiri* ou *Noto Naskh
  Arabic*), copiez-la sous `app\static\fonts\DocFont.ttf` (et `DocFont-Bold.ttf` pour le gras).
  Si aucune police arabe n'est trouvée, les libellés arabes sont simplement omis du PDF
  (la version imprimée depuis le navigateur les affiche toujours).

---

## Structure du projet

```
run.py                      Point d'entrée
requirements.txt
app/
  __init__.py               Fabrique d'application, filtres de templates
  config.py                 Configuration (base SQLite dans instance/)
  extensions.py             SQLAlchemy, protection CSRF
  models.py                 Modèles : Agency, Client, Vehicle, Contract, EngagementTemplate, Engagement
  seed.py                   Création des tables et données initiales
  utils.py                  Conversion des formulaires, numérotation, variables des modèles
  pdf.py                    Génération PDF (xhtml2pdf + police arabe)
  blueprints/
    main.py                 Tableau de bord
    clients.py              Clients
    vehicles.py             Véhicules
    contracts.py            Contrats (création, édition, duplication, clôture, PDF)
    engagements.py          Engagements et modèles d'engagement
    settings.py             Paramètres de l'agence
    api.py                  Autocomplétion des clients (JSON)
  templates/                Templates Jinja2 (un dossier par module)
  static/
    css/app.css             Styles de l'interface et de la feuille A4
    css/print.css           Feuille de style d'impression A4
    js/app.js               Autocomplétion, calcul des montants, modèles
    vendor/                 Bootstrap 5 et Bootstrap Icons (hors ligne)
tests/test_app.py           Tests automatisés (pytest)
```

## Sauvegarde

Toutes les données sont dans le fichier `instance\location.db`. Pour sauvegarder, arrêtez
l'application et copiez ce fichier :

```powershell
Copy-Item instance\location.db "sauvegarde-location-$(Get-Date -Format yyyy-MM-dd).db"
```

> Remarque : les tables sont créées automatiquement mais il n'y a pas d'outil de migration.
> Si vous modifiez `models.py` sur une base existante, sauvegardez-la puis adaptez le schéma
> (ou repartez d'une base vide).
