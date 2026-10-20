from importlib import import_module

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

# Même mot de passe initial que la migration du compte admin (« admin123 », à changer).
ADMIN_PASSWORD_HASH = import_module(
    'urban_infrastructure.users.migrations.0002_reset_admin_account',
).ADMIN_PASSWORD_HASH


class Command(BaseCommand):
    help = "Crée le compte « admin » si la base ne contient encore aucun administrateur."

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(Q(is_superuser=True) | Q(role='admin')).exists():
            self.stdout.write('Un administrateur existe déjà.')
            return

        User.objects.create(
            username='admin',
            email='kabir.niassef@gmail.com',
            password=ADMIN_PASSWORD_HASH,
            role='admin',
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS('Compte « admin » créé.'))
