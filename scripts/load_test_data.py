"""
Script pour populer la base de données avec des données de test
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from urban_infrastructure.users.models import CustomUser, UserRole
from urban_infrastructure.incidents.models import IncidentCategory, Incident
from urban_infrastructure.assets.models import AssetType, Asset, AssetHistory
from urban_infrastructure.interventions.models import Intervention

# Créer les catégories d'incidents
print("Création des catégories d'incidents...")
categories = [
    ('lighting', 'Éclairage Public'),
    ('road', 'Voirie'),
    ('waste', 'Déchets'),
    ('signal', 'Signalisation'),
]

for code, name in categories:
    IncidentCategory.objects.get_or_create(
        name=code,
        defaults={'description': name}
    )
print("✓ Catégories d'incidents créées")

# Créer les types d'actifs
print("Création des types d'actifs...")
asset_types = [
    ('lamp_post', 'Candélabre/Lampadaire'),
    ('traffic_light', 'Feu de Circulation'),
    ('sign', 'Panneau de Signalisation'),
    ('bench', 'Banc Public'),
]

for code, name in asset_types:
    AssetType.objects.get_or_create(
        name=code,
        defaults={'description': name}
    )
print("✓ Types d'actifs créés")

# Créer des utilisateurs de test
print("Création des utilisateurs de test...")
users_data = [
    {'username': 'citoyen1', 'email': 'citoyen@test.fr', 'role': 'citizen', 'name': 'Jean Dupont'},
    {'username': 'agent1', 'email': 'agent@test.fr', 'role': 'agent', 'name': 'Pierre Martin'},
    {'username': 'manager1', 'email': 'manager@test.fr', 'role': 'manager', 'name': 'Sophie Bernard'},
    {'username': 'decision1', 'email': 'decision@test.fr', 'role': 'decision_maker', 'name': 'Marie Lefevre'},
]

for user_data in users_data:
    username = user_data['username']
    if not CustomUser.objects.filter(username=username).exists():
        user = CustomUser.objects.create_user(
            username=username,
            email=user_data['email'],
            password='password123',
            role=user_data['role'],
            first_name=user_data['name'].split()[0],
            last_name=user_data['name'].split()[1] if len(user_data['name'].split()) > 1 else '',
        )
        print(f"  ✓ Utilisateur créé: {username}")

print("✓ Utilisateurs de test créés")

# Créer des incidents de test
print("Création des incidents de test...")
citoyen = CustomUser.objects.get(username='citoyen1')
lighting_category = IncidentCategory.objects.get(name='lighting')
road_category = IncidentCategory.objects.get(name='road')

incidents_data = [
    {
        'title': 'Lampadaire défectueux rue de Paris',
        'description': 'Le lampadaire au n°42 ne s\'allume plus',
        'category': lighting_category,
        'latitude': 48.8566,
        'longitude': 2.3522,
        'address': '42 Rue de Paris, 75000 Paris',
        'priority': 'high',
    },
    {
        'title': 'Nid de poule impasse du commerce',
        'description': 'Importante dégradation de la chaussée',
        'category': road_category,
        'latitude': 48.8646,
        'longitude': 2.3430,
        'address': 'Impasse du Commerce, 75011 Paris',
        'priority': 'medium',
    },
]

for incident_data in incidents_data:
    if not Incident.objects.filter(title=incident_data['title']).exists():
        Incident.objects.create(
            title=incident_data['title'],
            description=incident_data['description'],
            category=incident_data['category'],
            reporter=citoyen,
            latitude=incident_data['latitude'],
            longitude=incident_data['longitude'],
            address=incident_data['address'],
            priority=incident_data['priority'],
            status='created',
        )
        print(f"  ✓ Incident créé: {incident_data['title']}")

print("✓ Incidents de test créés")

# Créer des actifs de test
print("Création des actifs de test...")
lamp_type = AssetType.objects.get(name='lamp_post')

assets_data = [
    {
        'code': 'LAMP-001',
        'name': 'Lampadaire rue de Paris #42',
        'asset_type': lamp_type,
        'latitude': 48.8566,
        'longitude': 2.3522,
        'location': '42 Rue de Paris, 75000 Paris',
        'model': 'LED-500W',
        'brand': 'Philips',
        'installed_date': datetime.now().date(),
    },
]

for asset_data in assets_data:
    if not Asset.objects.filter(code=asset_data['code']).exists():
        Asset.objects.create(**asset_data)
        print(f"  ✓ Actif créé: {asset_data['code']}")

print("✓ Actifs de test créés")

print("\n✅ Données de test importées avec succès!")
print("\nComptes de test disponibles:")
print("  Admin: admin / admin123")
print("  Citoyen: citoyen1 / password123")
print("  Agent: agent1 / password123")
print("  Manager: manager1 / password123")
print("  Décideur: decision1 / password123")
