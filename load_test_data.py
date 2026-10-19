"""Script de peuplement de la base de données pour le projet GIU."""

import os
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from urban_infrastructure.assets.models import Asset, AssetType
from urban_infrastructure.incidents.models import Incident, IncidentCategory
from urban_infrastructure.users.models import CustomUser


def populate_test_data():
    """Crée les données de démonstration en environnement de développement."""
    if not settings.DEBUG:
        raise RuntimeError('Les données de démonstration ne peuvent pas être chargées en production.')

    admin = CustomUser.objects.filter(username='admin').first()
    admin_created = admin is None
    if admin is None:
        admin = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Kabir',
            last_name='Niasse',
            role='admin',
        )
        print('  [OK] Administrateur de démonstration créé')
    else:
        print('  [OK] Administrateur existant conservé sans modification')

    print('Création des catégories d\'incidents...')
    categories = [
        ('lighting', 'Éclairage Public'),
        ('road', 'Voirie'),
        ('waste', 'Déchets'),
        ('signal', 'Signalisation'),
        ('imprudence', 'Imprudence'),
        ('vitesse', 'Vitesse'),
        ('panne', 'Panne'),
        ('mauvaise_visibilite', 'Mauvaise visibilité'),
    ]
    for code, label in categories:
        IncidentCategory.objects.get_or_create(
            name=code,
            defaults={'description': label},
        )
    print("[OK] Catégories d'incidents créées")

    print('Création des types d\'actifs...')
    asset_types = [
        ('lamp_post', 'Candélabre/Lampadaire'),
        ('traffic_light', 'Feu de Circulation'),
        ('sign', 'Panneau de Signalisation'),
        ('bench', 'Banc Public'),
    ]
    for code, label in asset_types:
        AssetType.objects.get_or_create(
            name=code,
            defaults={'description': label},
        )
    print("[OK] Types d'actifs créés")

    print('Création des utilisateurs de test...')
    users_data = [
        {'username': 'citoyen1', 'email': 'citoyen@test.fr', 'role': 'citizen', 'name': 'Seynabou Niane'},
        {'username': 'agent1', 'email': 'agent@test.fr', 'role': 'agent', 'name': 'Fatou Gueye'},
        {'username': 'manager1', 'email': 'manager@test.fr', 'role': 'manager', 'name': 'Kabir Niasse'},
        {'username': 'decision1', 'email': 'decision@test.fr', 'role': 'decision_maker', 'name': 'Demo Niang'},
    ]
    for user_data in users_data:
        username = user_data['username']
        if not CustomUser.objects.filter(username=username).exists():
            CustomUser.objects.create_user(
                username=username,
                email=user_data['email'],
                password='password123',
                role=user_data['role'],
                first_name=user_data['name'].split()[0],
                last_name=user_data['name'].split()[1] if len(user_data['name'].split()) > 1 else '',
            )
            print(f"  [OK] Utilisateur créé: {username}")
    print("[OK] Utilisateurs de test créés")

    print('Création des incidents de test...')
    citoyen = CustomUser.objects.get(username='citoyen1')
    lighting_category = IncidentCategory.objects.get(name='lighting')
    road_category = IncidentCategory.objects.get(name='road')
    incidents_data = [
        {
            'title': 'Lampadaire défectueux rue de Paris',
            'description': 'Le lampadaire au n°42 ne s\'allume plus',
            'category': lighting_category,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
            'priority': 'high',
        },
        {
            'title': 'Nid de poule impasse du commerce',
            'description': 'Importante dégradation de la chaussée',
            'category': road_category,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
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
                region=incident_data['region'],
                department=incident_data['department'],
                commune=incident_data['commune'],
                priority=incident_data['priority'],
                status='created',
            )
            print(f"  [OK] Incident créé: {incident_data['title']}")
    print("[OK] Incidents de test créés")

    print('Création des actifs de test...')
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
            print(f"  [OK] Actif créé: {asset_data['code']}")
    print("[OK] Actifs de test créés")

    print('\n[OK] Données de test importées avec succès!')
    print('\nLes comptes existants ne sont pas modifiés.')
    if admin_created:
        print('Mot de passe initial de l’admin de démonstration: admin123 (à changer).')
    print('Les comptes de démonstration sont réservés au développement.')
    return True


if __name__ == '__main__':
    populate_test_data()
