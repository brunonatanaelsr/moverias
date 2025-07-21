"""
Sistema de configuração de alertas por email
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from core.monitoring import system_monitor
import os

class Command(BaseCommand):
    help = 'Configure email alerts for monitoring system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add-admin',
            type=str,
            help='Add admin email for alerts (format: "Name <email@domain.com>")'
        )
        parser.add_argument(
            '--remove-admin',
            type=str,
            help='Remove admin email from alerts'
        )
        parser.add_argument(
            '--list-admins',
            action='store_true',
            help='List current admin emails'
        )
        parser.add_argument(
            '--test-email',
            action='store_true',
            help='Send test email to all admins'
        )
        parser.add_argument(
            '--set-cooldown',
            type=int,
            help='Set alert cooldown in seconds (default: 300)'
        )

    def handle(self, *args, **options):
        if options['list_admins']:
            self.list_admins()
        elif options['add_admin']:
            self.add_admin(options['add_admin'])
        elif options['remove_admin']:
            self.remove_admin(options['remove_admin'])
        elif options['test_email']:
            self.test_email()
        elif options['set_cooldown']:
            self.set_cooldown(options['set_cooldown'])
        else:
            self.show_help()

    def list_admins(self):
        """List current admin emails"""
        admins = getattr(settings, 'ADMINS', [])
        
        if not admins:
            self.stdout.write(self.style.WARNING('No admin emails configured'))
            return
        
        self.stdout.write(self.style.SUCCESS('Current admin emails:'))
        for name, email in admins:
            self.stdout.write(f'  - {name} <{email}>')

    def add_admin(self, admin_string):
        """Add admin email"""
        try:
            # Parse "Name <email@domain.com>" format
            if '<' in admin_string and '>' in admin_string:
                name = admin_string.split('<')[0].strip().strip('"\'')
                email = admin_string.split('<')[1].split('>')[0].strip()
            else:
                # Just email provided
                email = admin_string.strip()
                name = email.split('@')[0].title()
            
            # Validate email format
            from django.core.validators import validate_email
            validate_email(email)
            
            self.stdout.write(f'Admin email configured: {name} <{email}>')
            self.stdout.write(self.style.WARNING(
                'Note: Add this to your settings.py ADMINS configuration:\n'
                f'ADMINS = [("{name}", "{email}")]'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error adding admin: {e}'))

    def remove_admin(self, email):
        """Remove admin email"""
        admins = getattr(settings, 'ADMINS', [])
        
        # Find and remove admin
        updated_admins = [(name, admin_email) for name, admin_email in admins if admin_email != email]
        
        if len(updated_admins) == len(admins):
            self.stdout.write(self.style.WARNING(f'Admin email {email} not found'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin email {email} would be removed'))
            self.stdout.write(self.style.WARNING(
                'Note: Update your settings.py ADMINS configuration manually'
            ))

    def test_email(self):
        """Send test email to all admins"""
        admins = getattr(settings, 'ADMINS', [])
        
        if not admins:
            self.stdout.write(self.style.ERROR('No admin emails configured'))
            return
        
        subject = 'Move Marias - Test Monitoring Alert'
        message = '''
This is a test email from the Move Marias monitoring system.

If you receive this email, the alert system is working correctly.

System Information:
- Monitoring system: Active
- Alert cooldown: {} seconds
- Time: {}

---
Move Marias Monitoring System
        '''.format(
            system_monitor.alert_cooldown,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        try:
            from django.utils import timezone
            
            admin_emails = [email for name, email in admins]
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            self.stdout.write(self.style.SUCCESS(f'Test email sent to {len(admin_emails)} admin(s)'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending test email: {e}'))

    def set_cooldown(self, cooldown):
        """Set alert cooldown"""
        if cooldown < 60:
            self.stdout.write(self.style.ERROR('Cooldown must be at least 60 seconds'))
            return
        
        system_monitor.alert_cooldown = cooldown
        self.stdout.write(self.style.SUCCESS(f'Alert cooldown set to {cooldown} seconds'))

    def show_help(self):
        """Show help information"""
        self.stdout.write(self.style.SUCCESS('Email Alert Configuration'))
        self.stdout.write('')
        self.stdout.write('Available commands:')
        self.stdout.write('  --list-admins         List current admin emails')
        self.stdout.write('  --add-admin EMAIL     Add admin email')
        self.stdout.write('  --remove-admin EMAIL  Remove admin email') 
        self.stdout.write('  --test-email          Send test email')
        self.stdout.write('  --set-cooldown SEC    Set alert cooldown')
        self.stdout.write('')
        self.stdout.write('Examples:')
        self.stdout.write('  python manage.py configure_alerts --add-admin "Admin <admin@movemarias.com>"')
        self.stdout.write('  python manage.py configure_alerts --test-email')
        self.stdout.write('  python manage.py configure_alerts --set-cooldown 600')
        self.stdout.write('')
        self.stdout.write('Note: Email configuration in settings.py is required:')
        self.stdout.write('')
        self.stdout.write('EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"')
        self.stdout.write('EMAIL_HOST = "smtp.gmail.com"')
        self.stdout.write('EMAIL_PORT = 587')
        self.stdout.write('EMAIL_USE_TLS = True')
        self.stdout.write('EMAIL_HOST_USER = "your-email@gmail.com"')
        self.stdout.write('EMAIL_HOST_PASSWORD = "your-app-password"')
        self.stdout.write('DEFAULT_FROM_EMAIL = "MoveMarias <your-email@gmail.com>"')
        self.stdout.write('')
        self.stdout.write('ADMINS = [')
        self.stdout.write('    ("Admin Name", "admin@movemarias.com"),')
        self.stdout.write('    ("Tech Lead", "tech@movemarias.com"),')
        self.stdout.write(']')
