from django.db import migrations


def create_lighting_category(apps, schema_editor):
    category_model = apps.get_model('incidents', 'IncidentCategory')
    category_model.objects.using(schema_editor.connection.alias).get_or_create(
        name='lighting',
        defaults={'description': 'Lampadaire / Éclairage public'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0006_add_flood_environment_categories'),
    ]

    operations = [
        migrations.RunPython(create_lighting_category, migrations.RunPython.noop),
    ]
