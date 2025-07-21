"""
Simple test command to verify system status
"""
from django.core.management.base import BaseCommand
from core.health_checks import run_all_health_checks
import json

class Command(BaseCommand):
    help = 'Test system status'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Running system health checks...'))
        
        try:
            health_results = run_all_health_checks()
            
            # Display results
            for check_name, result in health_results.items():
                if check_name == 'overall':
                    continue
                
                healthy = result.get('healthy', False)
                message = result.get('message', 'No message')
                
                status = '✓ PASS' if healthy else '✗ FAIL'
                style = self.style.SUCCESS if healthy else self.style.ERROR
                
                self.stdout.write(f'{check_name.upper()}: {style(status)} - {message}')
            
            # Overall status
            overall = health_results.get('overall', {})
            overall_healthy = overall.get('healthy', False)
            
            if overall_healthy:
                self.stdout.write(self.style.SUCCESS('\nOverall Health: ✓ HEALTHY'))
            else:
                self.stdout.write(self.style.ERROR('\nOverall Health: ✗ ISSUES DETECTED'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Health check failed: {str(e)}'))
