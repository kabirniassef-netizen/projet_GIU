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
python load_test_data.py

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

### Notifications WhatsApp (optionnelles)

Pour activer les notifications via WhatsApp Cloud API, configurez les secrets
`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` et
`WHATSAPP_TEMPLATE_NAME` dans l'environnement de déploiement. Le modèle doit
être approuvé par Meta et les contacts destinataires doivent avoir donné leur
consentement. Pour recevoir les événements de webhook, publiez
`/webhooks/whatsapp/` derrière HTTPS et configurez
`WHATSAPP_WEBHOOK_VERIFY_TOKEN` et `WHATSAPP_APP_SECRET`. Ne mettez aucune de
ces valeurs secrètes dans Git.

## 📚 Architecture

### Mise en ligne sur Render

Le fichier `render.yaml` décrit un service Django, une base PostgreSQL et un
disque persistant pour les photos. Il utilise des offres payantes afin que la
base et les fichiers ne reposent pas sur le stockage éphémère d'une offre
gratuite. Vérifiez les tarifs affichés par Render avant de créer les ressources.

1. Publiez le dépôt sur GitHub et connectez-le à votre compte Render.
2. Dans Render, choisissez **New > Blueprint**, sélectionnez ce dépôt et
   examinez les ressources et leur coût avant de confirmer leur création.
3. Une fois le service prêt, créez un administrateur avec
   `python manage.py createsuperuser` dans le Shell du service Render.
4. Testez l'inscription citoyen et l'envoi d'un signalement depuis un téléphone.
5. Configurez SMTP séparément si les courriels doivent être remis aux
   destinataires. Les notifications WhatsApp restent optionnelles.

Le Blueprint ne charge pas de comptes ou de données de démonstration en
production. Le déploiement automatique est désactivé; publiez explicitement les
changements après vérification. L'adresse initiale sera
`https://giu-signalements.onrender.com`; un domaine personnalisé pourra être
ajouté ensuite dans Render et dans `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.
Les avertissements HSTS sur les sous-domaines et le preload restent à évaluer
après le choix du domaine; ne les activez pas à l'aveugle.

### Stack Technique
- **Backend**: Django 6.0.6
- **API**: Django REST Framework 3.17
- **Base de données**: SQLite en développement, PostgreSQL configurable pour la production
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
│   └── notifications/               # Notifications et webhooks
├── templates/                       # Templates HTML
├── static/                          # Fichiers statiques (CSS, JS)
│   ├── css/style.css               # Styles
│   └── js/api.js                   # Client API
├── manage.py                        # CLI Django
├── load_test_data.py               # Script de données de test
└── requirements.txt                 # Dépendances Python
```

## 👥 Rôles Utilisateurs

### 1. **Citoyen**
- Signaler des anomalies urbaines
- Joindre des photos et renseigner la région, le département et la commune
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
# Méthode 1: Via l'interface Django
# Aller sur /admin/ et créer un utilisateur

# Méthode 2: Via l'API (à implémenter)
# POST /api/token/
# {
#   "username": "user",
#   "password": "password"
# }
```

### Utiliser le Token

```bash
curl -H "Authorization: Token votre_token" http://localhost:8000/api/incidents/incidents/
```

## 📋 Comptes de Test

Sur une base de développement neuve, `load_test_data.py` crée les comptes de
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
python load_test_data.py

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

La mise en production n'est pas encore réalisée. Il faut choisir un hébergeur,
générer une clé secrète dédiée, configurer `DEBUG=False`, `ALLOWED_HOSTS`,
PostgreSQL, CORS/CSRF, SMTP, HTTPS, un serveur WSGI et un reverse proxy. Les
contrôles Django se lancent avec `python manage.py check --deploy`; les erreurs
et avertissements doivent être traités avant la mise en ligne.

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

- [Guide du projet](docs/README.md)
- [Explication des diagrammes](docs/explication-diagrammes.md)
- [Document Word original](docs/explication-diagrammes.docx)

## 📧 Support

Pour toute question ou issue, veuillez consulter la documentation ou contacter l'administrateur système.

## 📄 Licence

Propriété de la municipalité. Tous droits réservés.

---

**Version:** 1.0.0  
**Dernière mise à jour:** 2026-06-30  
**Framework:** Django 6.0.6  
**État:** environnement local et tests prêts après configuration; déploiement de production restant à réaliser.
