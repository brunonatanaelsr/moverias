from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Clear all sessions and cache to fix CSRF issues'

    def handle(self, *args, **options):
        # Clear all sessions
        Session.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All sessions cleared'))
        
        # Clear cache
        cache.clear()
        self.stdout.write(self.style.SUCCESS('Cache cleared'))
        
        self.stdout.write(
            self.style.SUCCESS(
                'CSRF reset completed. Please clear browser cookies and restart server.'
            )
        )
