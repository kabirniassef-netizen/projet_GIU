from django.db import migrations, models

import urban_infrastructure.incidents.models


def populate_tracking_codes(apps, schema_editor):
    incident_model = apps.get_model('incidents', 'Incident')
    used_codes = set()
    for incident in incident_model.objects.using(schema_editor.connection.alias).filter(
        tracking_code__isnull=True,
    ):
        code = urban_infrastructure.incidents.models.generate_tracking_code()
        while code in used_codes:
            code = urban_infrastructure.incidents.models.generate_tracking_code()
        used_codes.add(code)
        incident.tracking_code = code
        incident.save(update_fields=['tracking_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0004_incident_reporter_name_incident_reporter_phone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='tracking_code',
            field=models.CharField(editable=False, max_length=12, null=True),
        ),
        migrations.RunPython(populate_tracking_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='incident',
            name='tracking_code',
            field=models.CharField(
                default=urban_infrastructure.incidents.models.generate_tracking_code,
                editable=False,
                max_length=12,
                unique=True,
            ),
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['status', 'created_at'], name='incidents_i_status_5d0930_idx'),
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['priority'], name='incidents_i_priorit_b2c75b_idx'),
        ),
    ]
