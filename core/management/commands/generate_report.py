"""
Management command for generating security and performance reports
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.reporting import generate_security_report, generate_performance_report, generate_all_reports
from core.health_checks import run_all_health_checks
import json
from pathlib import Path

class Command(BaseCommand):
    help = 'Generate security and performance reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['security', 'performance', 'health', 'all'],
            default='all',
            help='Type of report to generate'
        )
        parser.add_argument(
            '--output-format',
            choices=['json', 'summary'],
            default='summary',
            help='Output format'
        )
        parser.add_argument(
            '--save-only',
            action='store_true',
            help='Save report to file without displaying'
        )
    
    def handle(self, *args, **options):
        report_type = options['type']
        output_format = options['output_format']
        save_only = options['save_only']
        
        try:
            if report_type == 'security':
                self.generate_security_report(output_format, save_only)
            elif report_type == 'performance':
                self.generate_performance_report(output_format, save_only)
            elif report_type == 'health':
                self.generate_health_report(output_format, save_only)
            elif report_type == 'all':
                self.generate_all_reports(output_format, save_only)
            
        except Exception as e:
            raise CommandError(f'Failed to generate report: {str(e)}')
    
    def generate_security_report(self, output_format, save_only):
        """Generate security report"""
        self.stdout.write(self.style.SUCCESS('Generating security report...'))
        
        report_path, report_data = generate_security_report()
        
        if not save_only:
            if output_format == 'json':
                self.stdout.write(json.dumps(report_data, indent=2, default=str))
            else:
                self.display_security_summary(report_data)
        
        self.stdout.write(self.style.SUCCESS(f'Security report saved to: {report_path}'))
    
    def generate_performance_report(self, output_format, save_only):
        """Generate performance report"""
        self.stdout.write(self.style.SUCCESS('Generating performance report...'))
        
        report_path, report_data = generate_performance_report()
        
        if not save_only:
            if output_format == 'json':
                self.stdout.write(json.dumps(report_data, indent=2, default=str))
            else:
                self.display_performance_summary(report_data)
        
        self.stdout.write(self.style.SUCCESS(f'Performance report saved to: {report_path}'))
    
    def generate_health_report(self, output_format, save_only):
        """Generate health check report"""
        self.stdout.write(self.style.SUCCESS('Running health checks...'))
        
        health_results = run_all_health_checks()
        
        if not save_only:
            if output_format == 'json':
                self.stdout.write(json.dumps(health_results, indent=2, default=str))
            else:
                self.display_health_summary(health_results)
        
        # Save health report
        from django.conf import settings
        report_dir = Path(settings.BASE_DIR) / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        report_filename = f"health_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = report_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(health_results, f, indent=2, default=str)
        
        self.stdout.write(self.style.SUCCESS(f'Health report saved to: {report_path}'))
    
    def generate_all_reports(self, output_format, save_only):
        """Generate all reports"""
        self.stdout.write(self.style.SUCCESS('Generating all reports...'))
        
        reports = generate_all_reports()
        health_results = run_all_health_checks()
        
        if not save_only:
            if output_format == 'json':
                combined_data = {
                    'security': reports['security_report']['data'],
                    'performance': reports['performance_report']['data'],
                    'health': health_results
                }
                self.stdout.write(json.dumps(combined_data, indent=2, default=str))
            else:
                self.display_security_summary(reports['security_report']['data'])
                self.stdout.write('\n' + '='*50 + '\n')
                self.display_performance_summary(reports['performance_report']['data'])
                self.stdout.write('\n' + '='*50 + '\n')
                self.display_health_summary(health_results)
        
        self.stdout.write(self.style.SUCCESS('All reports generated:'))
        self.stdout.write(f'  Security: {reports["security_report"]["path"]}')
        self.stdout.write(f'  Performance: {reports["performance_report"]["path"]}')
    
    def display_security_summary(self, report_data):
        """Display security report summary"""
        self.stdout.write(self.style.SUCCESS('\n=== SECURITY REPORT SUMMARY ==='))
        
        # System info
        system_info = report_data.get('system_info', {})
        self.stdout.write(f'Debug Mode: {system_info.get("debug_mode", "Unknown")}')
        self.stdout.write(f'Database: {system_info.get("database_engine", "Unknown")}')
        self.stdout.write(f'Cache: {system_info.get("cache_backend", "Unknown")}')
        
        # Security checks
        self.stdout.write('\n--- Security Checks ---')
        security_checks = report_data.get('security_checks', {})
        
        for check_name, result in security_checks.items():
            status = '✓ PASS' if result else '✗ FAIL'
            style = self.style.SUCCESS if result else self.style.ERROR
            self.stdout.write(f'{check_name}: {style(status)}')
        
        # Password policy
        self.stdout.write('\n--- Password Policy ---')
        password_policy = report_data.get('password_policy', {})
        
        policy_score = sum(1 for v in password_policy.values() if v)
        total_checks = len(password_policy)
        
        if policy_score == total_checks:
            self.stdout.write(self.style.SUCCESS(f'Password policy: {policy_score}/{total_checks} checks passed'))
        else:
            self.stdout.write(self.style.WARNING(f'Password policy: {policy_score}/{total_checks} checks passed'))
        
        # User activity
        self.stdout.write('\n--- User Activity ---')
        user_activity = report_data.get('user_activity', {})
        
        self.stdout.write(f'Total users: {user_activity.get("total_users", 0)}')
        self.stdout.write(f'Active users (30 days): {user_activity.get("active_users_30_days", 0)}')
        self.stdout.write(f'Admin users: {user_activity.get("admin_users", 0)}')
        
        # Recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            self.stdout.write('\n--- Security Recommendations ---')
            for rec in recommendations[:5]:  # Show top 5
                priority_style = self.style.ERROR if rec['priority'] == 'high' else self.style.WARNING
                self.stdout.write(f'{priority_style(rec["priority"].upper())}: {rec["message"]}')
    
    def display_performance_summary(self, report_data):
        """Display performance report summary"""
        self.stdout.write(self.style.SUCCESS('\n=== PERFORMANCE REPORT SUMMARY ==='))
        
        # System resources
        system_resources = report_data.get('system_resources', {})
        if 'error' not in system_resources:
            self.stdout.write('\n--- System Resources ---')
            self.stdout.write(f'CPU Usage: {system_resources.get("cpu_percent", 0)}%')
            self.stdout.write(f'Memory Usage: {system_resources.get("memory_percent", 0)}%')
            self.stdout.write(f'Disk Usage: {system_resources.get("disk_percent", 0)}%')
            self.stdout.write(f'Available Memory: {system_resources.get("memory_available_gb", 0)} GB')
            self.stdout.write(f'Free Disk Space: {system_resources.get("disk_free_gb", 0)} GB')
        
        # Database performance
        db_performance = report_data.get('database_performance', {})
        if 'error' not in db_performance:
            self.stdout.write('\n--- Database Performance ---')
            self.stdout.write(f'Database Size: {db_performance.get("database_size_mb", 0)} MB')
            self.stdout.write(f'Table Count: {db_performance.get("table_count", 0)}')
            self.stdout.write(f'Connection Max Age: {db_performance.get("connection_max_age", 0)} seconds')
        
        # Cache performance
        cache_performance = report_data.get('cache_performance', {})
        if 'error' not in cache_performance:
            self.stdout.write('\n--- Cache Performance ---')
            cache_working = cache_performance.get('cache_working', False)
            status = '✓ Working' if cache_working else '✗ Not Working'
            style = self.style.SUCCESS if cache_working else self.style.ERROR
            self.stdout.write(f'Cache Status: {style(status)}')
            self.stdout.write(f'Cache Backend: {cache_performance.get("cache_backend", "Unknown")}')
        
        # Disk usage
        disk_usage = report_data.get('disk_usage', {})
        if 'error' not in disk_usage:
            self.stdout.write('\n--- Disk Usage by Directory ---')
            for directory, info in disk_usage.items():
                if isinstance(info, dict):
                    self.stdout.write(f'{directory}: {info.get("size_mb", 0)} MB ({info.get("file_count", 0)} files)')
        
        # Optimization suggestions
        suggestions = report_data.get('optimization_suggestions', [])
        if suggestions:
            self.stdout.write('\n--- Optimization Suggestions ---')
            for sug in suggestions[:5]:  # Show top 5
                priority_style = self.style.ERROR if sug['priority'] == 'high' else self.style.WARNING
                self.stdout.write(f'{priority_style(sug["priority"].upper())}: {sug["message"]}')
    
    def display_health_summary(self, health_results):
        """Display health check summary"""
        self.stdout.write(self.style.SUCCESS('\n=== HEALTH CHECK SUMMARY ==='))
        
        overall = health_results.get('overall', {})
        overall_healthy = overall.get('healthy', False)
        
        if overall_healthy:
            self.stdout.write(self.style.SUCCESS('Overall Health: ✓ HEALTHY'))
        else:
            self.stdout.write(self.style.ERROR('Overall Health: ✗ ISSUES DETECTED'))
        
        self.stdout.write('\n--- Individual Checks ---')
        
        for check_name, result in health_results.items():
            if check_name == 'overall':
                continue
            
            healthy = result.get('healthy', False)
            message = result.get('message', 'No message')
            
            status = '✓ PASS' if healthy else '✗ FAIL'
            style = self.style.SUCCESS if healthy else self.style.ERROR
            
            self.stdout.write(f'{check_name.upper()}: {style(status)} - {message}')
