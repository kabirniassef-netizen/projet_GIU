# 🏛️ Système de Gestion d'Infrastructure Urbaine

Un système pour gérer les infrastructures municipales urbaines, les signalements citoyens et les interventions techniques.

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.12+
- pip
- Virtual Environment

### Installation

```bash
# 1. Aller à la racine du dépôt
cd projet_GIU

# 2. Créer et activer l'environnement virtuel (Windows)
python -m venv .venv
.venv\Scripts\activate  # Windows

# Linux/macOS : source .venv/bin/activate

# 3. Copier la configuration locale (ne pas versionner .env)
Copy-Item .env.example .env  # PowerShell
# Linux/macOS : cp .env.example .env

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Appliquer les migrations
python manage.py migrate

# 6. Charger les données de démonstration (développement uniquement)
python scripts/load_test_data.py

# 7. Lancer le serveur de développement
python manage.py runserver
```

Accédez à l'application sur `http://localhost:8000`

La configuration fournie utilise SQLite pour le développement local. PostgreSQL
est disponible en définissant `DB_ENGINE=django.db.backends.postgresql` et les
variables `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` et `DB_PORT`.

## Notifications par e-mail

À chaque événement qui déclenche une notification dans l'application, un e-mail
est envoyé à chaque compte actif ayant une adresse e-mail renseignée. Les
adresses identiques reçoivent un seul message par événement. Les notifications
visibles dans l'application restent limitées aux utilisateurs concernés par
l'événement.
L'e-mail d'un nouveau signalement inclut son titre, sa description, son adresse,
sa catégorie et sa priorité ; lorsqu'elle est présente, la photo est intégrée
au corps HTML de l'e-mail.

En développement, les e-mails sont affichés dans la console du serveur Django,
ils ne sont pas remis aux boîtes de réception.
Pour envoyer de vrais e-mails, configurez les paramètres SMTP dans le fichier
local `.env` (ne publiez pas votre mot de passe SMTP) :

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-adresse@example.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-ou-mot-de-passe-application
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=votre-adresse@example.com
```

Pour Gmail, activez d'abord la validation en deux étapes du compte, puis créez
un nouveau mot de passe d'application. Révoquez tout ancien mot de passe
d'application qui aurait été exposé. Dans le `.env` local, ajoutez ce secret à
`EMAIL_HOST_PASSWORD`, puis remplacez `EMAIL_BACKEND` par
`django.core.mail.backends.smtp.EmailBackend`. Ne copiez jamais le secret dans
Git ou dans une conversation. Redémarrez ensuite le serveur Django et créez un
nouvel événement de test : les notifications passées ne sont pas renvoyées.

Pour voir les e-mails comme alertes sur le téléphone, installez l'application
Gmail, connectez le compte destinataire et activez ses notifications dans les
réglages Android/iOS et dans les réglages de notifications Gmail. Le téléphone
doit avoir accès à Internet. Le projet envoie les e-mails aux adresses des
comptes actifs; plusieurs comptes utilisant la même adresse reçoivent un seul
exemplaire par événement.

## 📚 Architecture

### Mise en ligne sur Render

L'application est en ligne sur https://giu-signalements.onrender.com, décrite
par `render.yaml`. Elle s'appuie uniquement sur des offres gratuites :

| Élément | Service | Variables à renseigner dans Render |
|---|---|---|
| Application Django (gunicorn) | Render, service web gratuit (Francfort) | `SECRET_KEY` (générée), `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` |
| Base PostgreSQL | Neon (gratuit, sans expiration) | `DATABASE_URL` (chaîne de connexion « pooled ») |
| Photos des signalements | Neon Object Storage (compatible S3, bucket privé `photos`) | `MEDIA_S3_ENDPOINT_URL`, `MEDIA_S3_REGION`, `MEDIA_S3_ACCESS_KEY_ID`, `MEDIA_S3_SECRET_ACCESS_KEY` |
| E-mails de notification | API Brevo | `BREVO_API_KEY`, `DEFAULT_FROM_EMAIL` |
| Chatbot (facultatif) | Typebot auto-hébergé, voir [docs/chatbot-typebot.md](docs/chatbot-typebot.md) | `TYPEBOT_ID`, `TYPEBOT_API_HOST`, `CHATBOT_API_KEY` |

Les variables doivent être ajoutées **sur le service web lui-même** (onglet
Environment), pas seulement dans un Environment Group non relié.

Points à connaître :

- **Déploiement manuel** : `autoDeploy` est désactivé. Après un `git push` sur
  `main`, lancez **Manual Deploy > Deploy latest commit** dans Render.
- **Démarrage** : chaque démarrage applique les migrations puis lance
  `ensure_admin`, qui crée le compte `admin` (mot de passe initial `admin123`)
  uniquement si la base ne contient encore aucun administrateur. Changez ce
  mot de passe immédiatement.
- **Mise en veille** : Render endort le service gratuit après 15 minutes sans
  trafic (environ 1 minute d'attente au réveil). Une tâche [cron-job.org](https://console.cron-job.org/)
  (`GIU keep-alive`) appelle `/health/` toutes les 10 minutes pour l'en
  empêcher. Cette route ne touche
  pas la base, ce qui laisse Neon se mettre en veille et préserve son quota.
- **Disque éphémère** : le disque de Render est effacé à chaque redémarrage ;
  c'est pourquoi les photos sont stockées chez Neon et non sur le serveur.
- **Erreurs** : les erreurs serveur (500) sont écrites dans l'onglet Logs du
  service Render.

Un domaine personnalisé peut être ajouté ensuite dans Render et dans
`ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`. Les réglages HSTS sur les
sous-domaines et le preload restent à évaluer après le choix du domaine.

### Stack Technique
- **Backend**: Django 6.0.6
- **API**: Django REST Framework 3.17
- **Base de données**: SQLite en développement, PostgreSQL (Neon) en production
- **Frontend**: HTML5/CSS3/JavaScript vanilla
- **Authentification**: Token-based + Session

### Structure du Projet

```
projet_GIU/
├── config/                          # Configuration Django
│   ├── settings.py                  # Paramètres de l'application
│   ├── urls.py                      # Routing
│   ├── views.py                     # Vues principales
│   └── wsgi.py                      # Déploiement
├── urban_infrastructure/            # Apps Django
│   ├── users/                       # Gestion des utilisateurs
│   ├── incidents/                   # Signalements d'incidents
│   ├── assets/                      # Patrimoine urbain
│   ├── interventions/               # Interventions techniques
│   ├── reports/                     # Rapports et KPI
│   └── notifications/               # Notifications in-app et e-mail
├── templates/                       # Templates HTML
├── static/                          # Fichiers statiques (CSS, JS)
│   ├── css/                         # Styles par page
│   └── js/                          # Client API et écrans
├── docs/                            # Diagrammes et explications
├── scripts/load_test_data.py        # Données de démonstration (DEBUG uniquement)
├── manage.py                        # CLI Django
└── requirements.txt                 # Dépendances Python
```

## 👥 Rôles Utilisateurs

### 1. **Citoyen**
- Signaler un accident de la route ou une anomalie urbaine après connexion ou création d'un compte citoyen
- Décrire les faits, préciser le point de repère, la région, le département et la commune, et joindre une photo facultative
- Suivre le statut de ses signalements en temps réel
- Consulter les statistiques publiques
- Participer aux consultations citoyennes

### 2. **Agent Technique**
- Recevoir les ordres de mission
- Consulter sa feuille de route
- Mettre à jour le statut des interventions sur le terrain
- Ajouter des rapports d'intervention avec photos

### 3. **Gestionnaire**
- Valider et qualifier les signalements
- Planifier les interventions
- Assigner les agents techniques
- Gérer l'inventaire du patrimoine urbain

### 4. **Décideur**
- Consulter le tableau de bord avec KPI
- Générer des rapports statistiques
- Analyser les tendances et performances

### 5. **Administrateur**
- Gérer tous les utilisateurs
- Configurer les paramètres du système
- Gérer les catégories d'incidents et les types d'actifs

## 📊 Modules Principaux

### 1. Gestion des Utilisateurs (`/api/users/`)
- CRUD complet des utilisateurs
- Attribution des rôles
- Authentification par Token

**Endpoints:**
- `GET /api/users/users/` - Lister les utilisateurs
- `POST /api/users/users/` - Créer un utilisateur
- `GET /api/users/users/{id}/` - Détails d'un utilisateur
- `GET /api/users/users/me/` - Profil actuel

### 2. Signalements d'Incidents (`/api/incidents/`)
Permet aux citoyens de signaler les anomalies urbaines.

**Endpoints:**
- `GET /api/incidents/incidents/` - Lister tous les incidents
- `POST /api/incidents/incidents/` - Créer un incident
- `GET /api/incidents/incidents/{id}/` - Détails d'un incident
- `POST /api/incidents/incidents/{id}/update_status/` - Mettre à jour le statut
- `GET /api/incidents/incidents/my_incidents/` - Mes incidents

**Modèle Incident:**
```json
{
  "title": "Lampadaire défectueux",
  "description": "Le lampadaire au n°42 ne s'allume plus",
  "category": "lighting",
  "region": "Île-de-France",
  "department": "Paris",
  "commune": "Paris",
  "photo": "file.jpg",
  "status": "created",
  "priority": "high"
}
```

**Statuts Incident:**
- `created` - Créé
- `validated` - Validé
- `planned` - Planifié
- `in_progress` - En cours
- `resolved` - Résolu
- `rejected` - Rejeté

### 3. Patrimoine Urbain (`/api/assets/`)
Inventaire complet des actifs urbains avec historique de maintenance.

**Endpoints:**
- `GET /api/assets/assets/` - Lister tous les actifs
- `POST /api/assets/assets/` - Créer un actif
- `GET /api/assets/types/` - Types d'actifs disponibles
- `GET /api/assets/history/` - Historique des actions

**Types d'Actifs:**
- Candélabre/Lampadaire
- Feu de Circulation
- Panneau de Signalisation
- Banc Public
- Corbeille à Déchets
- Arbres
- Vannes d'Eau
- Autres

### 4. Interventions Techniques (`/api/interventions/`)
Gestion complète du cycle de vie des interventions de maintenance.

**Endpoints:**
- `GET /api/interventions/interventions/` - Lister les interventions
- `POST /api/interventions/interventions/` - Créer une intervention
- `GET /api/interventions/interventions/my_interventions/` - Mes interventions
- `POST /api/interventions/interventions/{id}/update_status/` - Mettre à jour le statut

**Statuts Intervention:**
- `pending` - En attente
- `assigned` - Assignée
- `in_progress` - En cours
- `completed` - Complétée
- `cancelled` - Annulée

### 5. Rapports & KPI (`/api/reports/`)
Tableau de bord avec indicateurs de performance clés.

**Endpoints:**
- `GET /api/reports/reports/global_statistics/` - Statistiques globales
- `GET /api/reports/reports/incidents_by_status/` - Incidents par statut
- `GET /api/reports/reports/incidents_by_category/` - Incidents par catégorie
- `GET /api/reports/reports/kpi_summary/` - Résumé des KPI
- `GET /api/reports/reports/recent_incidents/` - Incidents récents
- `GET /api/reports/reports/pending_interventions/` - Interventions en attente

**KPI Disponibles:**
- Temps moyen de résolution des incidents
- Taux de disponibilité des équipements
- Coût moyen par intervention
- Efficacité des équipes
- Volume d'incidents par quartier

## 🔐 Authentification

### Obtenir un Token

```bash
# POST /api/auth/login/  (identifiant ou adresse e-mail)
curl -X POST http://localhost:8000/api/auth/login/   -H "Content-Type: application/json"   -d '{"username": "user", "password": "password"}'
# Réponse : {"token": "...", "user": {...}}
```

### Utiliser le Token

```bash
curl -H "Authorization: Token votre_token" http://localhost:8000/api/incidents/incidents/
```

## 📋 Comptes de Test

Sur une base de développement neuve, `scripts/load_test_data.py` crée les comptes de
démonstration ci-dessous. Il ne modifie pas les mots de passe des comptes
existants; l'admin nouvellement créé doit changer son mot de passe.

Ces identifiants sont réservés au développement et aux tests. Le script refuse
de fonctionner avec `DEBUG=False`; ne réutilisez jamais ces comptes en production.

| Rôle | Identifiant | Mot de passe |
|------|-------------|-------------|
| Admin | admin | admin123 |
| Citoyen | citoyen1 | password123 |
| Agent | agent1 | password123 |
| Manager | manager1 | password123 |
| Décideur | decision1 | password123 |

## 🛠️ Commandes Utiles

```bash
# Créer un superutilisateur
python manage.py createsuperuser

# Faire les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Charger les données de test
python scripts/load_test_data.py

# Lancer le shell Django
python manage.py shell

# Collecter les fichiers statiques
python manage.py collectstatic

# Vérifier la configuration de production (après configuration de .env)
python manage.py check --deploy

# Exécuter les tests API, métier et notifications
python manage.py test urban_infrastructure.users urban_infrastructure.notifications

# Serveur de développement
python manage.py runserver
```

## 📱 Cas d'Usage Principaux

### Cas 1: Signalement Citoyen
1. Citoyen crée un nouveau signalement via `/api/incidents/incidents/`
2. Citoyen joint une photo et renseigne la région, le département et la commune
3. Gestionnaire valide le signalement
4. Gestionnaire crée une intervention via `/api/interventions/interventions/`
5. Agent reçoit la mission et la traite
6. Agent met à jour le statut et envoie un rapport
7. Citoyen est notifié et peut suivre la résolution

### Cas 2: Maintenance Préventive
1. Manager planifie une intervention de maintenance
2. Créer une intervention avec une date planifiée
3. Assigner à un agent disponible
4. Agent complète la mission sur le terrain
5. Actif est mis à jour dans l'inventaire
6. Historique de maintenance est enregistré

### Cas 3: Analyse de Performance
1. Décideur accède au dashboard `/api/reports/reports/global_statistics/`
2. Consulte les KPI et les tendances
3. Identifie les zones problématiques
4. Prend des décisions basées sur les données

## 🚀 Déploiement

L'application est déployée sur Render : voir
[Mise en ligne sur Render](#mise-en-ligne-sur-render). Avant chaque mise en
ligne, lancez les tests et `python manage.py check --deploy` (avec la
configuration de production dans `.env`).

Reste à faire : héberger Typebot sur un VPS pour activer le chatbot en
production (Render gratuit ne convient pas, voir
[docs/chatbot-typebot.md](docs/chatbot-typebot.md)).

## 📝 Notes de Développement

### Points Clés à Considérer
- Les coordonnées GPS sont utilisées pour les actifs; les signalements demandent une adresse structurée
- Les graphiques du dashboard peuvent être ajoutés avec Chart.js
- L'upload de photos utilise Pillow pour validation
- La pagination est configurée par défaut sur 50 items

### Améliorations Futures
- Intégration d'une carte interactive (OpenStreetMap/Mapbox)
- Système de notifications en temps réel (WebSocket)
- Analyse prédictive (à cadrer, non implémentée)
- Application mobile native
- Intégration SMS/Email
- Export PDF des rapports

## 📚 Documentation

- [Explication des diagrammes](docs/explication-diagrammes.md)
- [Document Word original](docs/explication-diagrammes.docx)

## 📧 Support

Pour toute question ou issue, veuillez consulter la documentation ou contacter l'administrateur système.

## 📄 Licence

Propriété de la municipalité. Tous droits réservés.

---

**Version:** 1.0.0  
**Dernière mise à jour:** 2026-11-03  
**Framework:** Django 6.0.6  
**État:** en production sur Render (base et photos chez Neon) ; chatbot Typebot pas encore hébergé en production.

## Espace de travail (v2)

L'espace `/dashboard/` est une application monopage : navigation par rôle sans
rechargement, filtres et recherche synchronisés dans l'URL, tiroirs de détail,
thème clair/sombre et affichage mobile.

| Rôle | Fonctionnalités principales |
|---|---|
| Citoyen | Signalement avec photo et position GPS, suivi de ses signalements (code `GIU-XXXXXXXX`) |
| Agent | File de ses interventions, démarrage, clôture avec compte rendu et photo, journal d'entretien |
| Gestionnaire / Admin | Validation/rejet, priorisation, planification, réaffectation, annulation puis replanification, gestion des usagers et comptes (création, rôle, désactivation, mot de passe), export CSV |
| Décideur | Indicateurs, points d'attention, rapports périodiques, export CSV |

Pages publiques : `/signaler/` (signalement sans compte) et `/suivi/`
(suivi d'un signalement à partir de son code).

Variables d'environnement ajoutées :

```env
SHOW_DEMO_ACCOUNTS=False      # affiche les comptes de démo sur /login/ (par défaut = DEBUG)
SERVE_MEDIA=False             # sert /media/ sans DEBUG (démo sans stockage objet)
LOGIN_THROTTLE_RATE=20/minute # limite anti force brute sur /api/auth/login/
```

Après mise à jour : `python manage.py migrate` (ajoute le code de suivi aux
signalements existants et les types d'équipements).
