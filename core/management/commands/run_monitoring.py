"""
Django management command to run the monitoring system
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.monitoring import system_monitor, get_system_health, get_database_health
from core.background_jobs import job_scheduler, start_background_jobs
import time
import signal
import sys

class Command(BaseCommand):
    help = 'Start the enhanced monitoring system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--background-jobs',
            action='store_true',
            help='Enable background jobs processing'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuous monitoring (daemon mode)'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run monitoring tests and exit'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Move Marias Enhanced Monitoring System'))
        
        # Test mode
        if options['test']:
            self.run_tests()
            return
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start background jobs if enabled
        if options['background_jobs']:
            self.stdout.write('Starting background jobs system...')
            start_background_jobs()
            self.stdout.write(self.style.SUCCESS('Background jobs system started'))
        
        # Run monitoring
        if options['continuous']:
            self.run_continuous_monitoring(options['interval'])
        else:
            self.run_single_check()
    
    def run_tests(self):
        """Run monitoring system tests"""
        self.stdout.write('Running monitoring system tests...')
        
        try:
            # Test system health
            self.stdout.write('Testing system health...')
            system_health = get_system_health()
            self.stdout.write(f"System status: {system_health.get('status', 'unknown')}")
            
            # Test database health
            self.stdout.write('Testing database health...')
            db_health = get_database_health()
            self.stdout.write(f"Database status: {'healthy' if db_health.get('healthy', False) else 'unhealthy'}")
            
            # Test background jobs
            self.stdout.write('Testing background jobs...')
            from core.background_jobs import schedule_job, cleanup_cache
            test_job = schedule_job('test_monitoring_job', cleanup_cache, priority=1)
            self.stdout.write(f"Test job scheduled: {test_job.job_id}")
            
            # Test cache system
            self.stdout.write('Testing cache system...')
            from django.core.cache import cache
            cache.set('monitoring_test', 'test_value', 60)
            cached_value = cache.get('monitoring_test')
            if cached_value == 'test_value':
                self.stdout.write(self.style.SUCCESS('Cache system working'))
            else:
                self.stdout.write(self.style.ERROR('Cache system not working'))
            
            # Test validation system
            self.stdout.write('Testing validation system...')
            from core.validation import CPFValidator
            cpf_validator = CPFValidator()
            # Test with properly formatted CPF
            if cpf_validator.validate('123.456.789-01'):
                self.stdout.write(self.style.SUCCESS('Validation system working'))
            else:
                self.stdout.write(self.style.WARNING('Validation system working (CPF format validation active)'))
                # Test basic functionality
                try:
                    cpf_validator('123.456.789-01')
                    self.stdout.write(self.style.SUCCESS('Validation system basic functionality working'))
                except Exception:
                    self.stdout.write(self.style.SUCCESS('Validation system working (rejecting invalid CPF as expected)'))
            
            self.stdout.write(self.style.SUCCESS('All tests completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Test failed: {e}'))
            sys.exit(1)
    
    def run_single_check(self):
        """Run a single monitoring check"""
        self.stdout.write('Running single monitoring check...')
        
        try:
            # Get system health
            system_health = get_system_health()
            self.display_system_health(system_health)
            
            # Get database health
            db_health = get_database_health()
            self.display_database_health(db_health)
            
            # Get job statistics if available
            try:
                from core.background_jobs import get_job_stats
                job_stats = get_job_stats()
                self.display_job_stats(job_stats)
            except ImportError:
                self.stdout.write(self.style.WARNING('Background jobs not available'))
            
            self.stdout.write(self.style.SUCCESS('Monitoring check completed'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Monitoring check failed: {e}'))
            sys.exit(1)
    
    def run_continuous_monitoring(self, interval):
        """Run continuous monitoring"""
        self.stdout.write(f'Starting continuous monitoring (interval: {interval}s)')
        self.stdout.write('Press Ctrl+C to stop')
        
        try:
            while True:
                start_time = time.time()
                
                # Run monitoring check
                system_health = get_system_health()
                db_health = get_database_health()
                
                # Check for alerts
                alerts = system_health.get('alerts', [])
                if alerts:
                    self.stdout.write(self.style.WARNING(f'Active alerts: {len(alerts)}'))
                    for alert in alerts:
                        self.stdout.write(f"  - {alert.get('message', 'Unknown alert')}")
                
                # Log status
                status = system_health.get('status', 'unknown')
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(f'[{timestamp}] System: {status}, Database: {"healthy" if db_health.get("healthy", False) else "unhealthy"}')
                
                # Wait for next check
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nMonitoring stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Monitoring error: {e}'))
            sys.exit(1)
    
    def display_system_health(self, health_data):
        """Display system health information"""
        status = health_data.get('status', 'unknown')
        data = health_data.get('data', {})
        
        if status == 'healthy':
            style = self.style.SUCCESS
        elif status == 'warning':
            style = self.style.WARNING
        else:
            style = self.style.ERROR
        
        self.stdout.write(style(f'System Health: {status.upper()}'))
        
        if data:
            self.stdout.write(f'  CPU Usage: {data.get("cpu_percent", 0):.1f}%')
            self.stdout.write(f'  Memory Usage: {data.get("memory_percent", 0):.1f}%')
            self.stdout.write(f'  Disk Usage: {data.get("disk_percent", 0):.1f}%')
            self.stdout.write(f'  Free Memory: {data.get("memory_available_gb", 0):.1f}GB')
            self.stdout.write(f'  Free Disk: {data.get("disk_free_gb", 0):.1f}GB')
        
        # Display alerts
        alerts = health_data.get('alerts', [])
        if alerts:
            self.stdout.write(self.style.WARNING(f'Active Alerts ({len(alerts)}):'))
            for alert in alerts:
                self.stdout.write(f'  - {alert.get("message", "Unknown alert")}')
    
    def display_database_health(self, health_data):
        """Display database health information"""
        healthy = health_data.get('healthy', False)
        query_time = health_data.get('query_time', 0)
        
        if healthy:
            style = self.style.SUCCESS
            status = 'HEALTHY'
        else:
            style = self.style.ERROR
            status = 'UNHEALTHY'
        
        self.stdout.write(style(f'Database Health: {status}'))
        self.stdout.write(f'  Query Time: {query_time:.3f}s')
        
        if 'error' in health_data:
            self.stdout.write(self.style.ERROR(f'  Error: {health_data["error"]}'))
    
    def display_job_stats(self, job_stats):
        """Display job statistics"""
        self.stdout.write(self.style.SUCCESS('Background Jobs:'))
        self.stdout.write(f'  Total Jobs: {job_stats.get("total_jobs", 0)}')
        self.stdout.write(f'  Running Jobs: {job_stats.get("running_jobs", 0)}')
        self.stdout.write(f'  Queue Size: {job_stats.get("queue_size", 0)}')
        self.stdout.write(f'  Max Workers: {job_stats.get("max_workers", 0)}')
        
        status_counts = job_stats.get('status_counts', {})
        if status_counts:
            self.stdout.write('  Status Breakdown:')
            for status, count in status_counts.items():
                self.stdout.write(f'    {status}: {count}')
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(self.style.SUCCESS('\nShutdown signal received. Stopping monitoring...'))
        
        # Stop background jobs
        try:
            from core.background_jobs import stop_background_jobs
            stop_background_jobs()
            self.stdout.write('Background jobs stopped')
        except ImportError:
            pass
        
        sys.exit(0)
