"""
Security audit and compliance tools for MoveMarias
"""
import os
import re
import json
import logging
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import subprocess

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityAuditor:
    """Comprehensive security audit system"""
    
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'security_score': 0,
            'findings': [],
            'recommendations': [],
            'compliance_status': {}
        }
    
    def run_full_audit(self):
        """Run complete security audit"""
        logger.info("Starting comprehensive security audit")
        
        # Run all audit checks
        self.audit_django_settings()
        self.audit_password_policies()
        self.audit_permissions()
        self.audit_file_permissions()
        self.audit_dependencies()
        self.audit_database_security()
        self.audit_session_security()
        self.audit_csrf_protection()
        self.audit_xss_protection()
        self.audit_sql_injection_protection()
        self.audit_file_upload_security()
        self.audit_logging_security()
        
        # Calculate security score
        self.calculate_security_score()
        
        logger.info(f"Security audit completed. Score: {self.audit_results['security_score']}/100")
        return self.audit_results
    
    def audit_django_settings(self):
        """Audit Django security settings"""
        findings = []
        
        # Check DEBUG setting
        if settings.DEBUG:
            findings.append({
                'severity': 'HIGH',
                'category': 'Configuration',
                'finding': 'DEBUG is enabled in production',
                'recommendation': 'Set DEBUG = False in production'
            })
        
        # Check SECRET_KEY
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 50:
            findings.append({
                'severity': 'HIGH',
                'category': 'Configuration',
                'finding': 'SECRET_KEY is weak or missing',
                'recommendation': 'Use a strong, random SECRET_KEY with at least 50 characters'
            })
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
            findings.append({
                'severity': 'HIGH',
                'category': 'Configuration',
                'finding': 'ALLOWED_HOSTS is not properly configured',
                'recommendation': 'Set specific allowed hosts instead of using wildcard'
            })
        
        # Check SECURE_SSL_REDIRECT
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'HTTPS',
                'finding': 'SECURE_SSL_REDIRECT is not enabled',
                'recommendation': 'Enable SECURE_SSL_REDIRECT for HTTPS enforcement'
            })
        
        # Check SECURE_HSTS_SECONDS
        if not getattr(settings, 'SECURE_HSTS_SECONDS', 0):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'HTTPS',
                'finding': 'HSTS is not configured',
                'recommendation': 'Set SECURE_HSTS_SECONDS to enable HSTS'
            })
        
        # Check SECURE_CONTENT_TYPE_NOSNIFF
        if not getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Headers',
                'finding': 'X-Content-Type-Options header not set',
                'recommendation': 'Enable SECURE_CONTENT_TYPE_NOSNIFF'
            })
        
        # Check SECURE_BROWSER_XSS_FILTER
        if not getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Headers',
                'finding': 'X-XSS-Protection header not set',
                'recommendation': 'Enable SECURE_BROWSER_XSS_FILTER'
            })
        
        # Check X_FRAME_OPTIONS
        if not getattr(settings, 'X_FRAME_OPTIONS', ''):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Headers',
                'finding': 'X-Frame-Options header not set',
                'recommendation': 'Set X_FRAME_OPTIONS to DENY or SAMEORIGIN'
            })
        
        # Check CSRF settings
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'CSRF',
                'finding': 'CSRF cookie not secured',
                'recommendation': 'Set CSRF_COOKIE_SECURE = True'
            })
        
        # Check session settings
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Session',
                'finding': 'Session cookie not secured',
                'recommendation': 'Set SESSION_COOKIE_SECURE = True'
            })
        
        if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', False):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Session',
                'finding': 'Session cookie not HTTPOnly',
                'recommendation': 'Set SESSION_COOKIE_HTTPONLY = True'
            })
        
        self.audit_results['findings'].extend(findings)
        
        # Add recommendations
        if findings:
            self.audit_results['recommendations'].append({
                'category': 'Django Settings',
                'priority': 'HIGH',
                'recommendation': 'Review and update Django security settings according to best practices'
            })
    
    def audit_password_policies(self):
        """Audit password policies"""
        findings = []
        
        # Check password validators
        password_validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        
        required_validators = [
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            'django.contrib.auth.password_validation.MinimumLengthValidator',
            'django.contrib.auth.password_validation.CommonPasswordValidator',
            'django.contrib.auth.password_validation.NumericPasswordValidator'
        ]
        
        configured_validators = [v['NAME'] for v in password_validators]
        
        for validator in required_validators:
            if validator not in configured_validators:
                findings.append({
                    'severity': 'MEDIUM',
                    'category': 'Authentication',
                    'finding': f'Missing password validator: {validator}',
                    'recommendation': f'Add {validator} to AUTH_PASSWORD_VALIDATORS'
                })
        
        # Check for weak users
        weak_users = User.objects.filter(
            models.Q(password__icontains='123') |
            models.Q(password__icontains='password') |
            models.Q(password__icontains='admin')
        )
        
        if weak_users.exists():
            findings.append({
                'severity': 'HIGH',
                'category': 'Authentication',
                'finding': f'Found {weak_users.count()} users with potentially weak passwords',
                'recommendation': 'Force password reset for users with weak passwords'
            })
        
        self.audit_results['findings'].extend(findings)
    
    def audit_permissions(self):
        """Audit user permissions and roles"""
        findings = []
        
        # Check for excessive superusers
        superuser_count = User.objects.filter(is_superuser=True).count()
        if superuser_count > 5:
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Permissions',
                'finding': f'Too many superusers: {superuser_count}',
                'recommendation': 'Reduce number of superusers and use proper role-based permissions'
            })
        
        # Check for inactive users with permissions
        inactive_staff = User.objects.filter(is_active=False, is_staff=True)
        if inactive_staff.exists():
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Permissions',
                'finding': f'Found {inactive_staff.count()} inactive users with staff permissions',
                'recommendation': 'Remove staff permissions from inactive users'
            })
        
        # Check for users with never-used permissions
        # This would require tracking permission usage
        
        self.audit_results['findings'].extend(findings)
    
    def audit_file_permissions(self):
        """Audit file system permissions"""
        findings = []
        
        # Check sensitive files
        sensitive_files = [
            'manage.py',
            'movemarias/settings.py',
            'movemarias/urls.py',
            'db.sqlite3'
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                mode = oct(stat.st_mode)[-3:]
                
                if mode.endswith('7'):  # World writable
                    findings.append({
                        'severity': 'HIGH',
                        'category': 'File Permissions',
                        'finding': f'File {file_path} is world-writable',
                        'recommendation': f'Change permissions of {file_path} to remove world write access'
                    })
        
        # Check logs directory
        if os.path.exists('logs'):
            for root, dirs, files in os.walk('logs'):
                for file in files:
                    file_path = os.path.join(root, file)
                    stat = os.stat(file_path)
                    mode = oct(stat.st_mode)[-3:]
                    
                    if mode.endswith('7'):
                        findings.append({
                            'severity': 'MEDIUM',
                            'category': 'File Permissions',
                            'finding': f'Log file {file_path} is world-writable',
                            'recommendation': f'Secure log file permissions for {file_path}'
                        })
        
        self.audit_results['findings'].extend(findings)
    
    def audit_dependencies(self):
        """Audit dependencies for known vulnerabilities"""
        findings = []
        
        try:
            # Check for outdated packages
            result = subprocess.run(['pip', 'list', '--outdated'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                outdated_packages = result.stdout.strip().split('\n')[2:]  # Skip header
                if outdated_packages:
                    findings.append({
                        'severity': 'MEDIUM',
                        'category': 'Dependencies',
                        'finding': f'Found {len(outdated_packages)} outdated packages',
                        'recommendation': 'Update packages to latest versions and check for security updates'
                    })
        except:
            pass
        
        # Check for known vulnerable packages
        vulnerable_packages = [
            'django<4.0',
            'pillow<8.0',
            'requests<2.20'
        ]
        
        # This would require a more sophisticated vulnerability database
        
        self.audit_results['findings'].extend(findings)
    
    def audit_database_security(self):
        """Audit database security settings"""
        findings = []
        
        # Check database configuration
        db_config = settings.DATABASES.get('default', {})
        
        if db_config.get('ENGINE') == 'django.db.backends.sqlite3':
            db_path = db_config.get('NAME', 'db.sqlite3')
            if os.path.exists(db_path):
                stat = os.stat(db_path)
                mode = oct(stat.st_mode)[-3:]
                
                if mode.endswith('7'):
                    findings.append({
                        'severity': 'HIGH',
                        'category': 'Database',
                        'finding': 'Database file is world-writable',
                        'recommendation': 'Secure database file permissions'
                    })
        
        # Check for default database passwords
        if db_config.get('PASSWORD') in ['', 'password', 'admin', '123456']:
            findings.append({
                'severity': 'HIGH',
                'category': 'Database',
                'finding': 'Weak or default database password',
                'recommendation': 'Use strong database passwords'
            })
        
        self.audit_results['findings'].extend(findings)
    
    def audit_session_security(self):
        """Audit session security"""
        findings = []
        
        # Check session timeout
        session_timeout = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)  # 2 weeks default
        if session_timeout > 86400:  # More than 24 hours
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Session',
                'finding': 'Session timeout is too long',
                'recommendation': 'Reduce SESSION_COOKIE_AGE to improve security'
            })
        
        # Check session engine
        session_engine = getattr(settings, 'SESSION_ENGINE', 'django.contrib.sessions.backends.db')
        if session_engine == 'django.contrib.sessions.backends.file':
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Session',
                'finding': 'Using file-based sessions',
                'recommendation': 'Consider using database or cache-based sessions'
            })
        
        self.audit_results['findings'].extend(findings)
    
    def audit_csrf_protection(self):
        """Audit CSRF protection"""
        findings = []
        
        # Check CSRF middleware
        middleware = getattr(settings, 'MIDDLEWARE', [])
        if 'django.middleware.csrf.CsrfViewMiddleware' not in middleware:
            findings.append({
                'severity': 'HIGH',
                'category': 'CSRF',
                'finding': 'CSRF middleware not installed',
                'recommendation': 'Add django.middleware.csrf.CsrfViewMiddleware to MIDDLEWARE'
            })
        
        # Check CSRF exemptions
        # This would require code analysis to find @csrf_exempt decorators
        
        self.audit_results['findings'].extend(findings)
    
    def audit_xss_protection(self):
        """Audit XSS protection measures"""
        findings = []
        
        # Check for potential XSS in templates
        template_dirs = getattr(settings, 'TEMPLATES', [])
        for template_config in template_dirs:
            for template_dir in template_config.get('DIRS', []):
                if os.path.exists(template_dir):
                    self._scan_templates_for_xss(template_dir, findings)
        
        self.audit_results['findings'].extend(findings)
    
    def _scan_templates_for_xss(self, template_dir, findings):
        """Scan templates for potential XSS vulnerabilities"""
        xss_patterns = [
            r'\{\{.*\|safe\}\}',  # Django safe filter
            r'\{\{.*autoescape.*off.*\}\}',  # Autoescape off
            r'<script.*\{\{.*\}\}.*</script>',  # Script tags with variables
        ]
        
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            for pattern in xss_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    findings.append({
                                        'severity': 'MEDIUM',
                                        'category': 'XSS',
                                        'finding': f'Potential XSS vulnerability in {file_path}',
                                        'recommendation': f'Review template {file_path} for XSS vulnerabilities'
                                    })
                                    break
                    except:
                        pass
    
    def audit_sql_injection_protection(self):
        """Audit SQL injection protection"""
        findings = []
        
        # Check for raw SQL usage
        # This would require code analysis
        
        # Check for string formatting in queries
        # This would require static analysis
        
        self.audit_results['findings'].extend(findings)
    
    def audit_file_upload_security(self):
        """Audit file upload security"""
        findings = []
        
        # Check file upload settings
        max_upload_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440)  # 2.5MB
        if max_upload_size > 10485760:  # 10MB
            findings.append({
                'severity': 'MEDIUM',
                'category': 'File Upload',
                'finding': 'File upload size limit is too large',
                'recommendation': 'Reduce FILE_UPLOAD_MAX_MEMORY_SIZE to prevent DoS attacks'
            })
        
        # Check media files configuration
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        if media_root and not media_root.startswith('/'):
            findings.append({
                'severity': 'MEDIUM',
                'category': 'File Upload',
                'finding': 'MEDIA_ROOT uses relative path',
                'recommendation': 'Use absolute path for MEDIA_ROOT'
            })
        
        self.audit_results['findings'].extend(findings)
    
    def audit_logging_security(self):
        """Audit logging security"""
        findings = []
        
        # Check logging configuration
        logging_config = getattr(settings, 'LOGGING', {})
        
        if not logging_config:
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Logging',
                'finding': 'Logging not configured',
                'recommendation': 'Configure proper logging for security monitoring'
            })
        
        # Check for security-related loggers
        loggers = logging_config.get('loggers', {})
        security_loggers = ['django.security', 'django.request']
        
        for logger_name in security_loggers:
            if logger_name not in loggers:
                findings.append({
                    'severity': 'MEDIUM',
                    'category': 'Logging',
                    'finding': f'Missing security logger: {logger_name}',
                    'recommendation': f'Add {logger_name} logger for security monitoring'
                })
        
        self.audit_results['findings'].extend(findings)
    
    def calculate_security_score(self):
        """Calculate overall security score"""
        total_score = 100
        
        for finding in self.audit_results['findings']:
            if finding['severity'] == 'HIGH':
                total_score -= 15
            elif finding['severity'] == 'MEDIUM':
                total_score -= 5
            elif finding['severity'] == 'LOW':
                total_score -= 1
        
        self.audit_results['security_score'] = max(0, total_score)
    
    def generate_report(self):
        """Generate security audit report"""
        report = {
            'title': 'MoveMarias Security Audit Report',
            'generated_at': datetime.now().isoformat(),
            'security_score': self.audit_results['security_score'],
            'summary': {
                'total_findings': len(self.audit_results['findings']),
                'high_severity': len([f for f in self.audit_results['findings'] if f['severity'] == 'HIGH']),
                'medium_severity': len([f for f in self.audit_results['findings'] if f['severity'] == 'MEDIUM']),
                'low_severity': len([f for f in self.audit_results['findings'] if f['severity'] == 'LOW'])
            },
            'findings': self.audit_results['findings'],
            'recommendations': self.audit_results['recommendations']
        }
        
        return report


@require_http_methods(["GET"])
@staff_member_required
def security_audit_view(request):
    """API endpoint for security audit"""
    try:
        auditor = SecurityAuditor()
        audit_results = auditor.run_full_audit()
        
        return JsonResponse(audit_results)
    
    except Exception as e:
        logger.error(f"Error running security audit: {e}")
        return JsonResponse({
            'error': 'Failed to run security audit',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
@staff_member_required
def security_report_view(request):
    """Generate security report"""
    try:
        auditor = SecurityAuditor()
        auditor.run_full_audit()
        report = auditor.generate_report()
        
        return JsonResponse(report)
    
    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        return JsonResponse({
            'error': 'Failed to generate security report',
            'message': str(e)
        }, status=500)


class SecurityAuditCommand(BaseCommand):
    """Management command for security audit"""
    
    help = 'Run comprehensive security audit'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='security_audit_report.json',
            help='Output file for audit report'
        )
        
        parser.add_argument(
            '--format',
            choices=['json', 'html'],
            default='json',
            help='Output format'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting security audit...'))
        
        auditor = SecurityAuditor()
        audit_results = auditor.run_full_audit()
        
        # Generate report
        report = auditor.generate_report()
        
        # Save report
        output_file = options['output']
        output_format = options['format']
        
        if output_format == 'json':
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        elif output_format == 'html':
            html_report = self._generate_html_report(report)
            with open(output_file.replace('.json', '.html'), 'w') as f:
                f.write(html_report)
        
        # Print summary
        self.stdout.write(
            self.style.SUCCESS(f'Security audit completed. Score: {report["security_score"]}/100')
        )
        self.stdout.write(f'Report saved to: {output_file}')
        
        if report['summary']['high_severity'] > 0:
            self.stdout.write(
                self.style.WARNING(f'WARNING: {report["summary"]["high_severity"]} high severity findings!')
            )
    
    def _generate_html_report(self, report):
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .score {{ font-size: 24px; font-weight: bold; color: {'green' if report['security_score'] >= 80 else 'orange' if report['security_score'] >= 60 else 'red'}; }}
                .finding {{ margin: 10px 0; padding: 10px; border-left: 4px solid; }}
                .high {{ border-color: red; background-color: #ffebee; }}
                .medium {{ border-color: orange; background-color: #fff3e0; }}
                .low {{ border-color: yellow; background-color: #fffde7; }}
                .severity {{ font-weight: bold; }}
                .category {{ font-style: italic; }}
            </style>
        </head>
        <body>
            <h1>{report['title']}</h1>
            <p>Generated: {report['generated_at']}</p>
            <p class="score">Security Score: {report['security_score']}/100</p>
            
            <h2>Summary</h2>
            <ul>
                <li>Total Findings: {report['summary']['total_findings']}</li>
                <li>High Severity: {report['summary']['high_severity']}</li>
                <li>Medium Severity: {report['summary']['medium_severity']}</li>
                <li>Low Severity: {report['summary']['low_severity']}</li>
            </ul>
            
            <h2>Findings</h2>
        """
        
        for finding in report['findings']:
            severity_class = finding['severity'].lower()
            html += f"""
            <div class="finding {severity_class}">
                <div class="severity">{finding['severity']}</div>
                <div class="category">{finding['category']}</div>
                <div><strong>Finding:</strong> {finding['finding']}</div>
                <div><strong>Recommendation:</strong> {finding['recommendation']}</div>
            </div>
            """
        
        html += """
            </body>
        </html>
        """
        
        return html
