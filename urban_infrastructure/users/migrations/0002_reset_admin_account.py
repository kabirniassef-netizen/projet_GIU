from django.db import migrations

# Empreinte de « admin123 » : le mot de passe en clair n'est pas versionné.
ADMIN_PASSWORD_HASH = (
    'pbkdf2_sha256$1200000$gyBzaQXkFRJtJZ2NB7cFpx$'
    'wBKuWlJ7ysQc0iuwc1nyDeLXpLCj7eBmnfPVayhoLAI='
)


def reset_admin_account(apps, schema_editor):
    """Crée le compte « admin » sur le site hébergé et retire le compte « Kabir »."""
    CustomUser = apps.get_model('users', 'CustomUser')

    admin, _ = CustomUser.objects.get_or_create(
        username='admin',
        defaults={'email': 'kabir.niassef@gmail.com'},
    )
    admin.password = ADMIN_PASSWORD_HASH
    admin.role = 'admin'
    admin.is_superuser = True
    admin.is_staff = True
    admin.is_active = True
    admin.save()

    CustomUser.objects.filter(username='Kabir').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(reset_admin_account, migrations.RunPython.noop),
    ]
