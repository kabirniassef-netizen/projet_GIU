from django.db import migrations, models

NEW_CATEGORIES = [
    ('inondation', 'Inondation'),
    ('environnement', 'Environnement'),
]


def create_new_categories(apps, schema_editor):
    category_model = apps.get_model('incidents', 'IncidentCategory')
    for name, description in NEW_CATEGORIES:
        category_model.objects.using(schema_editor.connection.alias).get_or_create(
            name=name,
            defaults={'description': description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0005_incident_tracking_code_and_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incidentcategory',
            name='name',
            field=models.CharField(choices=[('lighting', 'Lampadaire / Éclairage public'), ('road', 'Voirie'), ('waste', 'Déchets'), ('signal', 'Signalisation'), ('water', 'Eau'), ('tree', 'Arbres'), ('bench', 'Mobilier Urbain'), ('other', 'Autre'), ('imprudence', 'Imprudence'), ('vitesse', 'Vitesse'), ('panne', 'Panne'), ('mauvaise_visibilite', 'Mauvaise visibilité'), ('accident', 'Accident de la route'), ('inondation', 'Inondation'), ('environnement', 'Environnement')], max_length=100, unique=True),
        ),
        migrations.RunPython(create_new_categories, migrations.RunPython.noop),
    ]
