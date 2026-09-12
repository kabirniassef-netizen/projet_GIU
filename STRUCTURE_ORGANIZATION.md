# 📂 Structure Organisée du Projet GIU

## 🎯 Vue d'ensemble

Le projet a été réorganisé pour une meilleure clarté et maintenabilité:

```
projet_GIU/
│
├── 📖 docs/                         ← DOCUMENTATION
│   ├── README.md                    (Ce fichier + guide complet)
│   ├── API_DOCUMENTATION.md         (API avec exemples curl)
│   ├── DELIVERY_SUMMARY.md          (Ce qui a été livré)
│   └── PROJECT_STRUCTURE.md         (Architecture détaillée)
│
├── 🔧 backend/                      ← CONFIGURATION DJANGO
│   └── (À mettre à jour)
│
├── 🎨 frontend/                     ← INTERFACE WEB
│   ├── templates/
│   │   ├── index.html               (Page d'accueil)
│   │   ├── dashboard.html           (Tableau de bord)
│   │   ├── login.html               (Connexion)
│   │   └── ...
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css            (Styles généraux)
│   │   │   ├── dashboard.css        (Styles dashboard)
│   │   │   └── landing.css          (Styles landing)
│   │   ├── js/
│   │   │   └── api.js               (Client API JavaScript)
│   │   └── images/                  (Ressources images)
│   └── (À mettre à jour)
│
├── 🚀 scripts/                      ← SCRIPTS UTILITAIRES
│   ├── load_test_data.py            (Charger données de test)
│   └── verify_setup.py              (Vérifier configuration)
│
├── ⚙️  utils/                        ← FICHIERS DE CONFIGURATION
│   ├── .env.example                 (Variables d'environnement)
│   └── requirements.txt             (Dépendances Python)
│
├── 💼 urban_infrastructure/         ← APPLICATIONS DJANGO
│   ├── __init__.py
│   ├── models.py
│   ├── router.py
│   ├── users/                       (Gestion des utilisateurs)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── permissions.py
│   │   └── migrations/
│   ├── incidents/                   (Signalements d'incidents)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── migrations/
│   ├── assets/                      (Patrimoine urbain)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── migrations/
│   ├── interventions/               (Interventions techniques)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── migrations/
│   └── reports/                     (Rapports & KPI)
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── admin.py
│       ├── apps.py
│       └── migrations/
│
├── 🔐 config/                       ← CONFIGURATION GLOBALE
│   ├── settings.py                  (Configuration Django)
│   ├── urls.py                      (Routage global)
│   ├── views.py                     (Vues principales)
│   ├── wsgi.py                      (Déploiement WSGI)
│   ├── asgi.py                      (Déploiement ASGI)
│   └── __init__.py
│
├── 📸 media/                        ← FICHIERS UPLOADÉS
│   └── (Images d'incidents, rapports, etc.)
│
├── 🐍 .venv/                        ← ENVIRONNEMENT VIRTUEL
│
├── 📚 .git/                         ← GIT (Historique)
│
├── ⚡ manage.py                     ← CLI DJANGO
│
├── 💾 db.sqlite3                    ← BASE DE DONNÉES
│
└── 📋 Autres fichiers
    ├── requirements.txt             (Dépendances)
    ├── .env.example                 (Exemple .env)
    ├── .gitignore                   (Git ignore)
    ├── READY.md                     (Statut du projet)
    └── WELCOME.txt                  (Bienvenue)
```

## 📖 Guide de Navigation

### Pour la Documentation
➡️ **Tout est maintenant dans le dossier `/docs/`**

| Fichier | Contenu |
|---------|---------|
| `docs/README.md` | Guide complet du projet |
| `docs/API_DOCUMENTATION.md` | API avec exemples curl |
| `docs/DELIVERY_SUMMARY.md` | Résumé de livraison |
| `docs/PROJECT_STRUCTURE.md` | Architecture complète |

### Pour le Code Backend
➡️ **Le code métier est dans `urban_infrastructure/`**

- `users/` - Gestion des utilisateurs et authentification
- `incidents/` - Signalements d'incidents
- `assets/` - Patrimoine urbain
- `interventions/` - Interventions techniques
- `reports/` - Rapports et KPI

### Pour l'Interface Web
➡️ **Tout est dans `frontend/`**

- `frontend/templates/` - Pages HTML
- `frontend/static/css/` - Feuilles de styles
- `frontend/static/js/` - Code JavaScript

### Pour les Scripts
➡️ **Les utilitaires sont dans `scripts/`**

```bash
# Charger les données de test
python scripts/load_test_data.py

# Vérifier la configuration
python scripts/verify_setup.py
```

## 🚀 Démarrage Rapide

```bash
# 1. Accéder au dossier
cd c:\Users\User\Desktop\projet_GIU

# 2. Activer l'environnement virtuel
.venv\Scripts\activate

# 3. Charger les données (optionnel, déjà fait)
python scripts/load_test_data.py

# 4. Lancer le serveur
python manage.py runserver

# 5. Accéder à l'application
http://localhost:8000
```

## 🔐 Comptes de Test

| Rôle | Utilisateur | Mot de passe |
|------|------------|------------|
| 👨‍💼 Admin | `admin` | `admin123` |
| 👤 Citoyen | `citoyen1` | `password123` |
| 🔧 Agent | `agent1` | `password123` |
| 📋 Manager | `manager1` | `password123` |
| 📊 Décideur | `decision1` | `password123` |

## 📍 Liens Rapides

| Service | URL |
|---------|-----|
| 🏠 Accueil | http://localhost:8000 |
| 👨‍💼 Admin | http://localhost:8000/admin/ |
| 🔗 API REST | http://localhost:8000/api/ |
| ⚠️ Incidents | http://localhost:8000/api/incidents/ |
| 🏗️ Actifs | http://localhost:8000/api/assets/ |
| 🔧 Interventions | http://localhost:8000/api/interventions/ |
| 📊 Rapports | http://localhost:8000/api/reports/ |

## 📦 Dépendances

Les dépendances sont listées dans `utils/requirements.txt`:

```bash
# Lire les dépendances
cat utils/requirements.txt

# Installer/mettre à jour
pip install -r utils/requirements.txt
```

## ⚙️ Configuration

La configuration se fait dans `config/settings.py`:

```python
# Base de données
DATABASES = {...}

# Applications installées
INSTALLED_APPS = [..., 'urban_infrastructure.users', ...]

# Authentification
AUTHENTICATION_BACKENDS = [...]

# API REST
REST_FRAMEWORK = {...}
```

Variables d'environnement dans `utils/.env.example`:

```bash
# Copier et configurer
cp utils/.env.example .env
```

## 🎯 Organisation Par Rôle

### 👨‍💻 Développeur Backend
→ Voir `urban_infrastructure/` et `config/`

### 🎨 Développeur Frontend
→ Voir `frontend/templates/` et `frontend/static/`

### 📚 Technicien Documentation
→ Voir `docs/`

### 🚀 DevOps / Déploiement
→ Voir `config/` et `utils/`

### 🧪 Testeur
→ Voir `scripts/` et la documentation

---

**Organisation créée pour la clarté et la maintenance optimale du projet! 🎉**
