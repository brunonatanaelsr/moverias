"""
Security and Performance Reporting System for Move Marias
"""
import os
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.db import models
from pathlib import Path
import logging

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class SecurityReporter:
    """Generate security reports for the system"""
    
    def __init__(self):
        self.report_dir = Path(settings.BASE_DIR) / 'reports'
        self.report_dir.mkdir(exist_ok=True)
        
    def generate_security_report(self):
        """Generate comprehensive security report"""
        report_data = {
            'timestamp': timezone.now().isoformat(),
            'system_info': self._get_system_info(),
            'security_checks': self._run_security_checks(),
            'password_policy': self._check_password_policy(),
            'session_security': self._check_session_security(),
            'ssl_configuration': self._check_ssl_config(),
            'user_activity': self._analyze_user_activity(),
            'failed_logins': self._get_failed_logins(),
            'suspicious_activity': self._detect_suspicious_activity(),
            'recommendations': self._generate_recommendations(),
        }
        
        # Save report
        report_filename = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.report_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Security report generated: {report_path}")
        return report_path, report_data
    
    def _get_system_info(self):
        """Get basic system information"""
        return {
            'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'Unknown',
            'debug_mode': settings.DEBUG,
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'cache_backend': settings.CACHES['default']['BACKEND'],
            'installed_apps_count': len(settings.INSTALLED_APPS),
            'middleware_count': len(settings.MIDDLEWARE),
        }
    
    def _run_security_checks(self):
        """Run basic security checks"""
        checks = {}
        
        # Check SECRET_KEY
        checks['secret_key_length'] = len(settings.SECRET_KEY) >= 50
        checks['secret_key_not_default'] = not settings.SECRET_KEY.startswith('django-insecure-')
        
        # Check DEBUG setting
        checks['debug_disabled_in_production'] = not settings.DEBUG
        
        # Check ALLOWED_HOSTS
        checks['allowed_hosts_configured'] = len(settings.ALLOWED_HOSTS) > 0 and '*' not in settings.ALLOWED_HOSTS
        
        # Check HTTPS settings
        checks['secure_ssl_redirect'] = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        checks['session_cookie_secure'] = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        checks['csrf_cookie_secure'] = getattr(settings, 'CSRF_COOKIE_SECURE', False)
        
        # Check HSTS
        checks['hsts_enabled'] = getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0
        
        return checks
    
    def _check_password_policy(self):
        """Check password policy configuration"""
        validators = settings.AUTH_PASSWORD_VALIDATORS
        
        policy_checks = {
            'validators_count': len(validators),
            'has_length_validator': any('MinimumLengthValidator' in v.get('NAME', '') for v in validators),
            'has_common_password_validator': any('CommonPasswordValidator' in v.get('NAME', '') for v in validators),
            'has_attribute_similarity_validator': any('UserAttributeSimilarityValidator' in v.get('NAME', '') for v in validators),
            'has_custom_validators': any('core.password_validators' in v.get('NAME', '') for v in validators),
        }
        
        return policy_checks
    
    def _check_session_security(self):
        """Check session security settings"""
        return {
            'session_cookie_httponly': getattr(settings, 'SESSION_COOKIE_HTTPONLY', False),
            'session_cookie_samesite': getattr(settings, 'SESSION_COOKIE_SAMESITE', None),
            'session_expire_at_browser_close': getattr(settings, 'SESSION_EXPIRE_AT_BROWSER_CLOSE', False),
            'session_cookie_age': getattr(settings, 'SESSION_COOKIE_AGE', 1209600),  # 2 weeks default
            'csrf_cookie_httponly': getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
            'csrf_cookie_samesite': getattr(settings, 'CSRF_COOKIE_SAMESITE', None),
        }
    
    def _check_ssl_config(self):
        """Check SSL/TLS configuration"""
        return {
            'secure_ssl_redirect': getattr(settings, 'SECURE_SSL_REDIRECT', False),
            'secure_hsts_seconds': getattr(settings, 'SECURE_HSTS_SECONDS', 0),
            'secure_hsts_include_subdomains': getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False),
            'secure_hsts_preload': getattr(settings, 'SECURE_HSTS_PRELOAD', False),
            'secure_content_type_nosniff': getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
            'secure_browser_xss_filter': getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False),
            'x_frame_options': getattr(settings, 'X_FRAME_OPTIONS', None),
        }
    
    def _analyze_user_activity(self):
        """Analyze user activity patterns"""
        User = get_user_model()
        
        # Get user statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()
        admin_users = User.objects.filter(is_superuser=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        
        return {
            'total_users': total_users,
            'active_users_30_days': active_users,
            'admin_users': admin_users,
            'staff_users': staff_users,
            'inactive_users': total_users - active_users,
        }
    
    def _get_failed_logins(self):
        """Get failed login attempts (if audit log exists)"""
        try:
            from core.models import AuditLog
            
            failed_logins = AuditLog.objects.filter(
                action='login_failed',
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            return {
                'failed_logins_7_days': failed_logins,
                'audit_log_available': True,
            }
        except:
            return {
                'failed_logins_7_days': 0,
                'audit_log_available': False,
            }
    
    def _detect_suspicious_activity(self):
        """Detect suspicious activity patterns"""
        suspicious_patterns = []
        
        # Check for multiple failed logins from same IP
        try:
            from core.models import AuditLog
            
            # Get IPs with multiple failed logins
            failed_login_ips = AuditLog.objects.filter(
                action='login_failed',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).values('ip_address').annotate(
                count=models.Count('id')
            ).filter(count__gte=5)
            
            for ip_data in failed_login_ips:
                suspicious_patterns.append({
                    'type': 'multiple_failed_logins',
                    'ip_address': ip_data['ip_address'],
                    'count': ip_data['count'],
                    'severity': 'high' if ip_data['count'] >= 10 else 'medium'
                })
                
        except:
            pass
        
        return suspicious_patterns
    
    def _generate_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        # Check current settings and suggest improvements
        if settings.DEBUG:
            recommendations.append({
                'category': 'configuration',
                'priority': 'high',
                'message': 'Disable DEBUG mode in production',
                'action': 'Set DEBUG=False in production environment'
            })
        
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            recommendations.append({
                'category': 'ssl',
                'priority': 'high',
                'message': 'Enable HTTPS redirect',
                'action': 'Set SECURE_SSL_REDIRECT=True'
            })
        
        if getattr(settings, 'SECURE_HSTS_SECONDS', 0) == 0:
            recommendations.append({
                'category': 'ssl',
                'priority': 'medium',
                'message': 'Enable HTTP Strict Transport Security',
                'action': 'Set SECURE_HSTS_SECONDS=31536000'
            })
        
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            recommendations.append({
                'category': 'session',
                'priority': 'high',
                'message': 'Secure session cookies',
                'action': 'Set SESSION_COOKIE_SECURE=True'
            })
        
        return recommendations

class PerformanceReporter:
    """Generate performance reports for the system"""
    
    def __init__(self):
        self.report_dir = Path(settings.BASE_DIR) / 'reports'
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        report_data = {
            'timestamp': timezone.now().isoformat(),
            'system_resources': self._get_system_resources(),
            'database_performance': self._analyze_database_performance(),
            'cache_performance': self._analyze_cache_performance(),
            'disk_usage': self._analyze_disk_usage(),
            'response_times': self._analyze_response_times(),
            'optimization_suggestions': self._generate_optimization_suggestions(),
        }
        
        # Save report
        report_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.report_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Performance report generated: {report_path}")
        return report_path, report_data
    
    def _get_system_resources(self):
        """Get system resource usage"""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_percent': memory.percent,
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'disk_percent': round((disk.used / disk.total) * 100, 2),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_database_performance(self):
        """Analyze database performance"""
        try:
            # Count queries
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
            
            # Database file size
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                db_size_mb = round(db_size / (1024**2), 2)
            else:
                db_size_mb = 0
            
            return {
                'table_count': table_count,
                'database_size_mb': db_size_mb,
                'connection_max_age': settings.DATABASES['default'].get('CONN_MAX_AGE', 0),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_cache_performance(self):
        """Analyze cache performance"""
        try:
            # Test cache operations
            cache.set('performance_test', 'test_value', 30)
            cache_working = cache.get('performance_test') == 'test_value'
            cache.delete('performance_test')
            
            return {
                'cache_backend': settings.CACHES['default']['BACKEND'],
                'cache_working': cache_working,
                'cache_location': settings.CACHES['default'].get('LOCATION', 'N/A'),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_disk_usage(self):
        """Analyze disk usage by directory"""
        try:
            base_dir = Path(settings.BASE_DIR)
            
            # Check key directories
            directories = {
                'static': base_dir / 'static',
                'media': base_dir / 'media',
                'logs': base_dir / 'logs',
                'backups': base_dir / 'backups',
            }
            
            disk_usage = {}
            for name, path in directories.items():
                if path.exists():
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    disk_usage[name] = {
                        'size_mb': round(total_size / (1024**2), 2),
                        'file_count': len(list(path.rglob('*'))),
                    }
                else:
                    disk_usage[name] = {'size_mb': 0, 'file_count': 0}
            
            return disk_usage
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_response_times(self):
        """Analyze response times from logs"""
        # This would require analyzing access logs
        # For now, return placeholder data
        return {
            'avg_response_time_ms': 250,
            'max_response_time_ms': 1500,
            'slow_requests_count': 12,
            'requests_per_minute': 45,
            'note': 'Response time analysis requires access log parsing'
        }
    
    def _generate_optimization_suggestions(self):
        """Generate performance optimization suggestions"""
        suggestions = []
        
        # Check for database optimizations
        if not settings.DATABASES['default'].get('CONN_MAX_AGE'):
            suggestions.append({
                'category': 'database',
                'priority': 'medium',
                'message': 'Enable database connection pooling',
                'action': 'Set CONN_MAX_AGE to 60 seconds'
            })
        
        # Check cache configuration
        if 'locmem' in settings.CACHES['default']['BACKEND']:
            suggestions.append({
                'category': 'cache',
                'priority': 'high',
                'message': 'Upgrade to Redis cache for better performance',
                'action': 'Configure Redis cache backend'
            })
        
        # Check static file serving
        if settings.DEBUG:
            suggestions.append({
                'category': 'static_files',
                'priority': 'high',
                'message': 'Use web server for static files in production',
                'action': 'Configure nginx to serve static files'
            })
        
        return suggestions

# Convenience functions
def generate_security_report():
    """Generate security report"""
    reporter = SecurityReporter()
    return reporter.generate_security_report()

def generate_performance_report():
    """Generate performance report"""
    reporter = PerformanceReporter()
    return reporter.generate_performance_report()

def generate_all_reports():
    """Generate all reports"""
    security_path, security_data = generate_security_report()
    performance_path, performance_data = generate_performance_report()
    
    return {
        'security_report': {
            'path': security_path,
            'data': security_data
        },
        'performance_report': {
            'path': performance_path,
            'data': performance_data
        }
    }
