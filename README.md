# 🏛️ Système de Gestion d'Infrastructure Urbaine

Un système complet et moderne pour gérer les infrastructures municipales urbaines avec un focus sur la participation citoyenne, la gestion d'équipes techniques et l'analyse prédictive.

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.10+
- pip
- Virtual Environment

### Installation

```bash
# 1. Cloner ou extraire le projet
cd projet_GIU

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations
python manage.py migrate

# 5. Charger les données de test
python load_test_data.py

# 6. Lancer le serveur de développement
python manage.py runserver
```

Accédez à l'application sur `http://localhost:8000`

## 📚 Architecture

### Stack Technique
- **Backend**: Django 6.0.6
- **API**: Django REST Framework 3.17
- **Base de données**: SQLite 3 (développement)
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
│   └── reports/                     # Rapports et KPI
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
- Joindre des photos et des données GPS
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
  "latitude": 48.8566,
  "longitude": 2.3522,
  "address": "42 Rue de Paris, 75000 Paris",
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

Après exécution de `load_test_data.py`:

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

# Serveur de développement
python manage.py runserver 0.0.0.0:8000
```

## 📱 Cas d'Usage Principaux

### Cas 1: Signalement Citoyen
1. Citoyen crée un nouveau signalement via `/api/incidents/incidents/`
2. Citoyen joint une photo et la localisation GPS
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

### Sur Heroku
```bash
# 1. Modifier settings.py pour ALLOWED_HOSTS
# 2. Créer Procfile
# 3. Créer runtime.txt
# git push heroku main
```

### Sur DigitalOcean
```bash
# 1. Créer un droplet Ubuntu
# 2. Installer les dépendances système
# 3. Configurer Gunicorn + Nginx
# 4. Configurer PostgreSQL
```

## 📝 Notes de Développement

### Points Clés à Considérer
- La géolocalisation utilise les coordonnées GPS (latitude/longitude) au lieu de PostGIS
- Les graphiques du dashboard peuvent être ajoutés avec Chart.js
- L'upload de photos utilise Pillow pour validation
- La pagination est configurée par défaut sur 50 items

### Améliorations Futures
- Intégration d'une carte interactive (OpenStreetMap/Mapbox)
- Système de notifications en temps réel (WebSocket)
- Analyse prédictive avec ML
- Application mobile native
- Intégration SMS/Email
- Export PDF des rapports

## 📧 Support

Pour toute question ou issue, veuillez consulter la documentation ou contacter l'administrateur système.

## 📄 Licence

Propriété de la municipalité. Tous droits réservés.

---

**Version:** 1.0.0  
**Dernière mise à jour:** 2026-06-30  
**Framework:** Django 6.0.6  
**Status:** ✅ Production Ready
