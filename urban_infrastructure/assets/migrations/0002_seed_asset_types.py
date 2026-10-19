from django.db import migrations


ASSET_TYPES = [
    ('lamp_post', 'Candélabre/Lampadaire'),
    ('traffic_light', 'Feu de Circulation'),
    ('sign', 'Panneau de Signalisation'),
    ('bench', 'Banc Public'),
    ('bin', 'Corbeille à Déchets'),
    ('tree', 'Arbre'),
    ('water_valve', "Vanne d'Eau"),
    ('manhole', 'Chambre de Visite'),
    ('other', 'Autre'),
]


def seed_asset_types(apps, schema_editor):
    asset_type_model = apps.get_model('assets', 'AssetType')
    database = schema_editor.connection.alias
    for code, label in ASSET_TYPES:
        asset_type_model.objects.using(database).get_or_create(
            name=code,
            defaults={'description': label},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_asset_types, migrations.RunPython.noop),
    ]
