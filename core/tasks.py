"""
Celery tasks for Move Marias system
"""
import os
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog
from .backup import BackupManager

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def backup_database(self):
    """
    Backup database task
    """
    try:
        backup_manager = BackupManager()
        backup_file = backup_manager.create_backup()
        
        logger.info(f"Database backup created: {backup_file}")
        
        # Clean old backups (keep last 7 days)
        backup_manager.cleanup_old_backups(days=7)
        
        return f"Backup successful: {backup_file}"
        
    except Exception as exc:
        logger.error(f"Database backup failed: {exc}")
        # Retry after 1 minute, 5 minutes, 15 minutes
        retry_countdown = [60, 300, 900][self.request.retries]
        raise self.retry(exc=exc, countdown=retry_countdown)

@shared_task(bind=True, max_retries=3)
def send_email_notification(self, subject, message, recipient_list, html_message=None):
    """
    Send email notification task
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {len(recipient_list)} recipients")
        return f"Email sent to {len(recipient_list)} recipients"
        
    except Exception as exc:
        logger.error(f"Email sending failed: {exc}")
        # Retry after 2 minutes, 10 minutes, 30 minutes
        retry_countdown = [120, 600, 1800][self.request.retries]
        raise self.retry(exc=exc, countdown=retry_countdown)

@shared_task
def cleanup_audit_logs():
    """
    Clean up old audit logs (keep last 90 days)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        
        deleted_count = AuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old audit logs")
        return f"Cleaned up {deleted_count} audit logs"
        
    except Exception as exc:
        logger.error(f"Audit log cleanup failed: {exc}")
        raise

@shared_task
def generate_report(report_type, user_id, parameters=None):
    """
    Generate system reports
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        
        if report_type == 'member_activity':
            # Generate member activity report
            report_data = _generate_member_activity_report(parameters)
        elif report_type == 'system_health':
            # Generate system health report
            report_data = _generate_system_health_report(parameters)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Save report or send email
        logger.info(f"Report '{report_type}' generated for user {user.email}")
        
        return f"Report '{report_type}' generated successfully"
        
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        raise

@shared_task
def check_system_health():
    """
    Check system health and send alerts if needed
    """
    try:
        health_issues = []
        
        # Check database connection
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            health_issues.append(f"Database connection failed: {e}")
        
        # Check Redis connection
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 30)
            if cache.get('health_check') != 'ok':
                health_issues.append("Redis cache not responding")
        except Exception as e:
            health_issues.append(f"Redis connection failed: {e}")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            if free / total < 0.1:  # Less than 10% free
                health_issues.append(f"Low disk space: {free/1024/1024/1024:.2f}GB free")
        except Exception as e:
            health_issues.append(f"Disk space check failed: {e}")
        
        if health_issues:
            # Send alert email to admins
            subject = "Move Marias - System Health Alert"
            message = "System health issues detected:\n\n" + "\n".join(health_issues)
            
            admin_emails = [
                email for name, email in settings.ADMINS
            ]
            
            if admin_emails:
                send_email_notification.delay(
                    subject=subject,
                    message=message,
                    recipient_list=admin_emails
                )
            
            logger.warning(f"System health issues: {health_issues}")
            return f"Health issues detected: {len(health_issues)}"
        
        logger.info("System health check passed")
        return "System health OK"
        
    except Exception as exc:
        logger.error(f"System health check failed: {exc}")
        raise

def _generate_member_activity_report(parameters):
    """
    Generate member activity report
    """
    # Implementation for member activity report
    pass

def _generate_system_health_report(parameters):
    """
    Generate system health report
    """
    # Implementation for system health report
    pass

# Periodic tasks configuration
CELERY_BEAT_SCHEDULE = {
    'backup-database': {
        'task': 'core.tasks.backup_database',
        'schedule': 60.0 * 60.0 * 24.0,  # Daily at midnight
    },
    'cleanup-audit-logs': {
        'task': 'core.tasks.cleanup_audit_logs',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # Weekly
    },
    'system-health-check': {
        'task': 'core.tasks.check_system_health',
        'schedule': 60.0 * 30.0,  # Every 30 minutes
    },
}
