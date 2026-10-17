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
python scripts/load_test_data.py

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

## 👥 Rôles Utilisateurs

### 1. **Citoyen**
- Signaler des anomalies urbaines
- Joindre des photos et renseigner la région, le département et la commune
- Suivre le statut de ses signalements en temps réel
- Consulter les statistiques publiques

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

### 1. Gestion des Utilisateurs
- CRUD complet des utilisateurs
- Attribution des rôles
- Authentification par Token

### 2. Signalements d'Incidents
Permet aux citoyens de signaler les anomalies urbaines avec géolocalisation.

**Statuts:** Créé → Validé → Planifié → En cours → Résolu

### 3. Patrimoine Urbain
Inventaire complet des actifs urbains avec historique de maintenance.

### 4. Interventions Techniques
Création et planification d'interventions avec affectation aux agents.

### 5. Rapports et KPI
Tableau de bord analytique avec statistiques et tendances.

## 📁 Structure du Projet

```
projet_GIU/
├── docs/                            # 📖 Documentation
│   ├── README.md                    # Ce fichier
│   ├── API_DOCUMENTATION.md         # Documentation API détaillée
│   ├── DELIVERY_SUMMARY.md          # Résumé de livraison
│   ├── PROJECT_STRUCTURE.md         # Architecture complète
│   └── QUICK_START.md               # Démarrage rapide
│
├── backend/                         # 🔧 Configuration Django
│   └── (À mettre à jour)
│
├── frontend/                        # 🎨 Interface Web
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── (À mettre à jour)
│
├── scripts/                         # 🚀 Scripts utilitaires
│   ├── load_test_data.py           # Charger les données de test
│   └── verify_setup.py              # Vérifier la configuration
│
├── utils/                           # ⚙️ Fichiers de configuration
│   ├── .env.example                # Exemple de variables d'env
│   └── requirements.txt             # Dépendances Python
│
├── urban_infrastructure/            # 💼 Applications Django
│   ├── users/                       # Gestion des utilisateurs
│   ├── incidents/                   # Signalements d'incidents
│   ├── assets/                      # Patrimoine urbain
│   ├── interventions/               # Interventions techniques
│   └── reports/                     # Rapports et KPI
│
├── config/                          # 🔐 Configuration globale
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
│
├── media/                           # 📸 Fichiers médias uploadés
├── .venv/                           # 🐍 Environnement virtuel
├── manage.py                        # Django CLI
└── db.sqlite3                       # Base de données
```

## 🔐 Comptes de Test

| Rôle | Utilisateur | Mot de passe |
|------|------------|------------|
| Admin | `admin` | `admin123` |
| Citoyen | `citoyen1` | `password123` |
| Agent | `agent1` | `password123` |
| Manager | `manager1` | `password123` |
| Décideur | `decision1` | `password123` |

## 📍 Accès Rapides

- **Accueil**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin/
- **API REST**: http://localhost:8000/api/
- **Incidents**: http://localhost:8000/api/incidents/
- **Actifs**: http://localhost:8000/api/assets/
- **Interventions**: http://localhost:8000/api/interventions/
- **Rapports**: http://localhost:8000/api/reports/

## 📖 Documentation Disponible

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Documentation API avancée avec exemples curl
- [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md) - Ce qui a été livré
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture complète du projet

## ✅ 34 Endpoints API Fonctionnels

**Utilisateurs** (6) | **Incidents** (8) | **Actifs** (7) | **Interventions** (7) | **Rapports** (6)

Voir [API_DOCUMENTATION.md](API_DOCUMENTATION.md) pour les détails.
