"""Create or update the superuser without typing the password on the console.

Credentials come from the environment or from ``.env``; nothing is hardcoded
in ``settings.py``. Run it with::

    python manage.py bootstrap_admin
"""

import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

BASE_DIR = settings.BASE_DIR


def read_setting(name, default=None):
    """Read a value from the environment and then from the local ``.env``."""
    value = os.environ.get(name)
    if value:
        return value
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for raw_line in env_file.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, env_value = line.partition('=')
            if key.strip() == name:
                return env_value.strip().strip('"').strip("'")
    return default


class Command(BaseCommand):
    help = 'Create the superuser of the project using the credentials of .env.'

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()

        username = read_setting('ADMIN_USERNAME', 'admin')
        email = read_setting('ADMIN_EMAIL', 'admin@example.com')
        password = read_setting('ADMIN_PASSWORD')

        if not password:
            generated = secrets.token_urlsafe(12)
            self.stdout.write(
                self.style.WARNING(
                    'ADMIN_PASSWORD is not set, so a random password was '
                    'generated. Save it now, it will not be shown again:'
                )
            )
            self.stdout.write(self.style.SUCCESS(f'  {username} / {generated}'))
            password = generated

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} superuser "{username}" ({email}). '
                'Log in at /admin/ with the password above.'
            )
        )

        if not user.check_password(password):
            raise CommandError('The password could not be set.')
