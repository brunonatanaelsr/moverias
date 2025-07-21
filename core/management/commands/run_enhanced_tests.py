"""
Django management command to run enhanced tests
"""
from django.core.management.base import BaseCommand
from django.test.utils import get_runner
from django.conf import settings
import sys
import time

class Command(BaseCommand):
    help = 'Run enhanced tests for the Move Marias system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--module',
            type=str,
            help='Specific test module to run (e.g., core.tests_enhanced)'
        )
        parser.add_argument(
            '--performance',
            action='store_true',
            help='Run performance tests only'
        )
        parser.add_argument(
            '--integration',
            action='store_true',
            help='Run integration tests only'
        )
        parser.add_argument(
            '--monitoring',
            action='store_true',
            help='Run monitoring tests only'
        )
        parser.add_argument(
            '--validation',
            action='store_true',
            help='Run validation tests only'
        )
        parser.add_argument(
            '--cache',
            action='store_true',
            help='Run cache tests only'
        )
        parser.add_argument(
            '--jobs',
            action='store_true',
            help='Run background jobs tests only'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Enhanced Test Suite'))
        
        # Set test runner
        test_runner_class = get_runner(settings)
        test_runner = test_runner_class(verbosity=2 if options['verbose'] else 1)
        
        # Determine which tests to run
        test_labels = self.get_test_labels(options)
        
        if not test_labels:
            # Run all enhanced tests
            test_labels = ['core.tests_enhanced']
        
        self.stdout.write(f'Running tests: {", ".join(test_labels)}')
        
        # Run tests
        start_time = time.time()
        result = test_runner.run_tests(test_labels)
        end_time = time.time()
        
        # Display results
        self.display_results(result, end_time - start_time)
        
        # Exit with appropriate code
        if result:
            sys.exit(1)
        else:
            sys.exit(0)
    
    def get_test_labels(self, options):
        """Get test labels based on options"""
        labels = []
        
        if options['module']:
            labels.append(options['module'])
        
        if options['performance']:
            labels.append('core.tests_enhanced.PerformanceTests')
        
        if options['integration']:
            labels.append('core.tests_enhanced.IntegrationTests')
        
        if options['monitoring']:
            labels.append('core.tests_enhanced.MonitoringSystemTests')
        
        if options['validation']:
            labels.append('core.tests_enhanced.ValidationSystemTests')
        
        if options['cache']:
            labels.append('core.tests_enhanced.CacheSystemTests')
        
        if options['jobs']:
            labels.append('core.tests_enhanced.BackgroundJobsTests')
        
        return labels
    
    def display_results(self, result, duration):
        """Display test results"""
        if result == 0:
            self.stdout.write(self.style.SUCCESS(f'All tests passed in {duration:.2f} seconds'))
        else:
            self.stdout.write(self.style.ERROR(f'Tests failed ({result} failures) in {duration:.2f} seconds'))
        
        # Additional system check
        self.run_system_check()
    
    def run_system_check(self):
        """Run a quick system check"""
        self.stdout.write('\nRunning system check...')
        
        try:
            # Check monitoring system
            from core.monitoring import get_system_health, get_database_health
            
            system_health = get_system_health()
            db_health = get_database_health()
            
            if system_health.get('status') != 'error':
                self.stdout.write(self.style.SUCCESS('✓ Monitoring system operational'))
            else:
                self.stdout.write(self.style.ERROR('✗ Monitoring system error'))
            
            if db_health.get('healthy', False):
                self.stdout.write(self.style.SUCCESS('✓ Database connection healthy'))
            else:
                self.stdout.write(self.style.ERROR('✗ Database connection issue'))
            
            # Check cache system
            from django.core.cache import cache
            cache.set('test_key', 'test_value', 10)
            if cache.get('test_key') == 'test_value':
                self.stdout.write(self.style.SUCCESS('✓ Cache system operational'))
            else:
                self.stdout.write(self.style.ERROR('✗ Cache system issue'))
            
            # Check validation system
            from core.validation import CPFValidator
            validator = CPFValidator()
            if validator.validate('12345678901'):
                self.stdout.write(self.style.SUCCESS('✓ Validation system operational'))
            else:
                self.stdout.write(self.style.ERROR('✗ Validation system issue'))
            
            # Check background jobs (if available)
            try:
                from core.background_jobs import get_job_stats
                job_stats = get_job_stats()
                if isinstance(job_stats, dict):
                    self.stdout.write(self.style.SUCCESS('✓ Background jobs system operational'))
                else:
                    self.stdout.write(self.style.WARNING('⚠ Background jobs system not fully operational'))
            except ImportError:
                self.stdout.write(self.style.WARNING('⚠ Background jobs system not available'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'System check failed: {e}'))
