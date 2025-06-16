"""
Management command for Celery operations
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from celery import current_app
from core.tasks import backup_database, cleanup_audit_logs, check_system_health
from core.health_checks import run_all_health_checks
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage Celery tasks and workers'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show Celery worker status')
        
        # Health command
        health_parser = subparsers.add_parser('health', help='Run health checks')
        
        # Tasks command
        tasks_parser = subparsers.add_parser('tasks', help='List or run tasks')
        tasks_parser.add_argument('--run', choices=['backup', 'cleanup', 'health-check'], 
                                help='Run a specific task')
        
        # Workers command
        workers_parser = subparsers.add_parser('workers', help='Manage workers')
        workers_parser.add_argument('--action', choices=['list', 'stats'], 
                                  default='list', help='Worker action')
    
    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'celery_manage')
            return
        
        if action == 'status':
            self.show_status()
        elif action == 'health':
            self.run_health_checks()
        elif action == 'tasks':
            self.manage_tasks(options)
        elif action == 'workers':
            self.manage_workers(options)
        else:
            raise CommandError(f'Unknown action: {action}')
    
    def show_status(self):
        """Show Celery system status"""
        self.stdout.write(self.style.SUCCESS('=== Celery Status ==='))
        
        try:
            celery_app = current_app
            inspect = celery_app.control.inspect()
            
            # Active workers
            active_workers = inspect.active()
            if active_workers:
                self.stdout.write(f"Active workers: {len(active_workers)}")
                for worker_name, tasks in active_workers.items():
                    self.stdout.write(f"  - {worker_name}: {len(tasks)} active tasks")
            else:
                self.stdout.write(self.style.WARNING("No active workers found"))
            
            # Scheduled tasks
            scheduled_tasks = inspect.scheduled()
            if scheduled_tasks:
                total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
                self.stdout.write(f"Scheduled tasks: {total_scheduled}")
            
            # Reserved tasks
            reserved_tasks = inspect.reserved()
            if reserved_tasks:
                total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())
                self.stdout.write(f"Reserved tasks: {total_reserved}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to get Celery status: {e}"))
    
    def run_health_checks(self):
        """Run system health checks"""
        self.stdout.write(self.style.SUCCESS('=== Health Checks ==='))
        
        results = run_all_health_checks()
        
        for check_name, result in results.items():
            if check_name == 'overall':
                continue
                
            status_style = self.style.SUCCESS if result['healthy'] else self.style.ERROR
            status_text = "✓ PASS" if result['healthy'] else "✗ FAIL"
            
            self.stdout.write(f"{check_name.upper()}: {status_style(status_text)} - {result['message']}")
        
        # Overall status
        overall = results['overall']
        overall_style = self.style.SUCCESS if overall['healthy'] else self.style.ERROR
        self.stdout.write(f"\nOVERALL: {overall_style(overall['message'])}")
    
    def manage_tasks(self, options):
        """Manage Celery tasks"""
        run_task = options.get('run')
        
        if run_task:
            self.run_task(run_task)
        else:
            self.list_tasks()
    
    def run_task(self, task_name):
        """Run a specific task"""
        self.stdout.write(f"Running task: {task_name}")
        
        try:
            if task_name == 'backup':
                result = backup_database.delay()
                self.stdout.write(f"Backup task queued: {result.id}")
                
            elif task_name == 'cleanup':
                result = cleanup_audit_logs.delay()
                self.stdout.write(f"Cleanup task queued: {result.id}")
                
            elif task_name == 'health-check':
                result = check_system_health.delay()
                self.stdout.write(f"Health check task queued: {result.id}")
                
            else:
                raise CommandError(f"Unknown task: {task_name}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to queue task: {e}"))
    
    def list_tasks(self):
        """List available tasks"""
        self.stdout.write(self.style.SUCCESS('=== Available Tasks ==='))
        
        tasks = [
            ('backup', 'Create encrypted database backup'),
            ('cleanup', 'Clean up old audit logs'),
            ('health-check', 'Run system health checks'),
        ]
        
        for task_name, description in tasks:
            self.stdout.write(f"  {task_name}: {description}")
        
        self.stdout.write("\nRun with --run TASK_NAME to execute a task")
    
    def manage_workers(self, options):
        """Manage Celery workers"""
        worker_action = options.get('action', 'list')
        
        try:
            celery_app = current_app
            inspect = celery_app.control.inspect()
            
            if worker_action == 'list':
                self.list_workers(inspect)
            elif worker_action == 'stats':
                self.show_worker_stats(inspect)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to get worker info: {e}"))
    
    def list_workers(self, inspect):
        """List active workers"""
        self.stdout.write(self.style.SUCCESS('=== Active Workers ==='))
        
        active_workers = inspect.active()
        
        if not active_workers:
            self.stdout.write("No active workers found")
            return
        
        for worker_name, tasks in active_workers.items():
            self.stdout.write(f"\nWorker: {worker_name}")
            self.stdout.write(f"  Active tasks: {len(tasks)}")
            
            for task in tasks[:3]:  # Show first 3 tasks
                self.stdout.write(f"    - {task.get('name', 'Unknown')} ({task.get('id', 'No ID')})")
            
            if len(tasks) > 3:
                self.stdout.write(f"    ... and {len(tasks) - 3} more tasks")
    
    def show_worker_stats(self, inspect):
        """Show worker statistics"""
        self.stdout.write(self.style.SUCCESS('=== Worker Statistics ==='))
        
        stats = inspect.stats()
        
        if not stats:
            self.stdout.write("No worker statistics available")
            return
        
        for worker_name, worker_stats in stats.items():
            self.stdout.write(f"\nWorker: {worker_name}")
            
            # Basic info
            if 'broker' in worker_stats:
                broker_info = worker_stats['broker']
                self.stdout.write(f"  Broker: {broker_info.get('transport', 'Unknown')}")
            
            # Pool info
            if 'pool' in worker_stats:
                pool_info = worker_stats['pool']
                self.stdout.write(f"  Pool: {pool_info.get('implementation', 'Unknown')}")
                self.stdout.write(f"  Processes: {pool_info.get('max-concurrency', 'Unknown')}")
            
            # Task counts
            if 'total' in worker_stats:
                total_stats = worker_stats['total']
                for key, value in total_stats.items():
                    if isinstance(value, (int, float)):
                        self.stdout.write(f"  {key.replace('_', ' ').title()}: {value}")
