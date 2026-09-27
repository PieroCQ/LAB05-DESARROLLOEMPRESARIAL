"""Create the "editores" group and a user that belongs to it.

The group can add and change movies, and add and change ratings, but it can
never delete a record. Run it with::

    python manage.py bootstrap_editor
"""

import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

BASE_DIR = settings.BASE_DIR

EDITOR_GROUP = 'editores'

# Codename -> app label of the permissions the group must have.
GROUP_PERMISSIONS = [
    ('add_movie', 'movies'),
    ('change_movie', 'movies'),
    ('view_movie', 'movies'),
    ('add_rating', 'movies'),
    ('change_rating', 'movies'),
    ('view_rating', 'movies'),
    ('view_genre', 'movies'),
    ('view_person', 'movies'),
]

# Codenames the group must NOT have, to make the restriction explicit.
FORBIDDEN_CODENAMES = ['delete_movie', 'delete_rating']


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
    help = 'Create the "editores" group and a test user with restricted access.'

    @transaction.atomic
    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=EDITOR_GROUP)

        for codename, app_label in GROUP_PERMISSIONS:
            permission = Permission.objects.get(codename=codename, content_type__app_label=app_label)
            group.permissions.add(permission)

        group.permissions.remove(
            *Permission.objects.filter(
                content_type__app_label='movies',
                codename__in=FORBIDDEN_CODENAMES,
            )
        )

        username = read_setting('EDITOR_USERNAME', 'editor')
        email = read_setting('EDITOR_EMAIL', 'editor@example.com')
        password = read_setting('EDITOR_PASSWORD')

        if not password:
            password = secrets.token_urlsafe(12)
            self.stdout.write(
                self.style.WARNING(
                    'EDITOR_PASSWORD is not set, so a random password was '
                    'generated. Save it now, it will not be shown again:'
                )
            )
            self.stdout.write(self.style.SUCCESS(f'  {username} / {password}'))

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={'email': email},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = False
        user.set_password(password)
        user.save()

        user.groups.set([group])
        # A stale superuser flag would bypass every permission of the group.
        if created and user.is_superuser:
            user.is_superuser = False
            user.save(update_fields=['is_superuser'])

        granted = sorted(group.permissions.values_list('codename', flat=True))
        self.stdout.write(
            self.style.SUCCESS(
                f'Group "{EDITOR_GROUP}" with {len(granted)} permissions: '
                f'{", ".join(granted)}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Created" if created else "Updated"} user "{username}" '
                f'(is_superuser={user.is_superuser}). Log in at /admin/.'
            )
        )
