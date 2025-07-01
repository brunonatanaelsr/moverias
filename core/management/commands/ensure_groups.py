"""
Management command to ensure required groups exist in the system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from core.permissions import ensure_groups_exist


class Command(BaseCommand):
    help = 'Ensure required groups exist in the system'

    def handle(self, *args, **options):
        self.stdout.write('Creating required groups...')
        
        ensure_groups_exist()
        
        # List all groups
        groups = Group.objects.all()
        self.stdout.write(f'Available groups: {", ".join([g.name for g in groups])}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully ensured all required groups exist')
        )
