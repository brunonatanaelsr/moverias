"""
Monitoring Dashboard Views - Enhanced with Background Jobs
"""
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta
import json
import time
import logging

from .monitoring import get_system_health, get_database_health, get_full_system_status, system_monitor, database_monitor

# Try to import background jobs
try:
    from .background_jobs import job_scheduler, get_job_stats
    BACKGROUND_JOBS_AVAILABLE = True
except ImportError:
    BACKGROUND_JOBS_AVAILABLE = False

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger('movemarias')

# Basic health check endpoints
@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """Basic health check endpoint"""
    return HttpResponse("OK", content_type="text/plain")

@never_cache
@require_http_methods(["GET"])
def health_detailed(request):
    """Detailed health check with system information"""
    start_time = time.time()
    
    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_data['checks']['database'] = {'status': 'healthy', 'response_time': 0}
    except Exception as e:
        health_data['checks']['database'] = {'status': 'error', 'error': str(e)}
        health_data['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_data['checks']['cache'] = {'status': 'healthy'}
    except Exception as e:
        health_data['checks']['cache'] = {'status': 'error', 'error': str(e)}
        health_data['status'] = 'unhealthy'
    
    # System health check
    try:
        system_health = get_system_health()
        health_data['checks']['system'] = system_health
    except Exception as e:
        health_data['checks']['system'] = {'status': 'error', 'error': str(e)}
        health_data['status'] = 'unhealthy'
    
    health_data['response_time'] = time.time() - start_time
    
    return JsonResponse(health_data, encoder=DjangoJSONEncoder)

# Enhanced Monitoring Dashboard Views

@method_decorator(staff_member_required, name='dispatch')
class MonitoringDashboardView(View):
    """Main monitoring dashboard"""
    
    def get(self, request):
        """Render monitoring dashboard"""
        context = {
            'page_title': 'System Monitoring',
            'system_health': get_system_health(),
            'database_health': get_database_health(),
            'current_time': timezone.now(),
            'background_jobs_available': BACKGROUND_JOBS_AVAILABLE,
            'psutil_available': PSUTIL_AVAILABLE
        }
        
        if BACKGROUND_JOBS_AVAILABLE:
            context['job_stats'] = get_job_stats()
        
        return render(request, 'monitoring/dashboard.html', context)

@method_decorator(staff_member_required, name='dispatch')
class SystemHealthAPIView(View):
    """API endpoint for system health data"""
    
    def get(self, request):
        """Get current system health"""
        try:
            health_data = get_full_system_status()
            return JsonResponse(health_data, encoder=DjangoJSONEncoder)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(staff_member_required, name='dispatch')
class MonitoringHistoryAPIView(View):
    """API endpoint for monitoring history"""
    
    def get(self, request):
        """Get monitoring history"""
        try:
            hours = int(request.GET.get('hours', 24))
            history_data = system_monitor.get_monitoring_data(hours)
            return JsonResponse({'data': history_data}, encoder=DjangoJSONEncoder)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(staff_member_required, name='dispatch')
class SystemStatsAPIView(View):
    """API endpoint for system statistics"""
    
    def get(self, request):
        """Get system statistics"""
        try:
            system_stats = system_monitor.get_system_stats()
            db_stats = database_monitor.get_database_stats()
            
            return JsonResponse({
                'system': system_stats,
                'database': db_stats,
                'timestamp': timezone.now()
            }, encoder=DjangoJSONEncoder)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(staff_member_required, name='dispatch')
class BackgroundJobsAPIView(View):
    """API endpoint for background jobs"""
    
    def get(self, request):
        """Get background jobs information"""
        if not BACKGROUND_JOBS_AVAILABLE:
            return JsonResponse({'error': 'Background jobs not available'}, status=503)
            
        try:
            job_stats = get_job_stats()
            
            # Get recent jobs
            recent_jobs = []
            for job_id, job in list(job_scheduler.jobs.items())[-10:]:  # Last 10 jobs
                recent_jobs.append(job.to_dict())
            
            return JsonResponse({
                'stats': job_stats,
                'recent_jobs': recent_jobs,
                'timestamp': timezone.now()
            }, encoder=DjangoJSONEncoder)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request):
        """Handle job actions"""
        if not BACKGROUND_JOBS_AVAILABLE:
            return JsonResponse({'error': 'Background jobs not available'}, status=503)
            
        try:
            data = json.loads(request.body)
            action = data.get('action')
            job_id = data.get('job_id')
            
            if action == 'cancel' and job_id:
                success = job_scheduler.cancel_job(job_id)
                return JsonResponse({'success': success})
            
            elif action == 'cleanup':
                days = int(data.get('days', 7))
                cleaned = job_scheduler.cleanup_old_jobs(days)
                return JsonResponse({'success': True, 'cleaned_jobs': cleaned})
            
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(staff_member_required, name='dispatch')
class MonitoringConfigView(View):
    """Monitoring configuration view"""
    
    def get(self, request):
        """Show monitoring configuration"""
        context = {
            'page_title': 'Monitoring Configuration',
            'thresholds': system_monitor.thresholds,
            'alert_cooldown': system_monitor.alert_cooldown,
        }
        
        if BACKGROUND_JOBS_AVAILABLE:
            context['max_workers'] = job_scheduler.max_workers
        
        return render(request, 'monitoring/config.html', context)
    
    def post(self, request):
        """Update monitoring configuration"""
        try:
            # Update thresholds
            if 'cpu_threshold' in request.POST:
                system_monitor.thresholds['cpu_percent'] = int(request.POST['cpu_threshold'])
            if 'memory_threshold' in request.POST:
                system_monitor.thresholds['memory_percent'] = int(request.POST['memory_threshold'])
            if 'disk_threshold' in request.POST:
                system_monitor.thresholds['disk_percent'] = int(request.POST['disk_threshold'])
            
            # Update alert cooldown
            if 'alert_cooldown' in request.POST:
                system_monitor.alert_cooldown = int(request.POST['alert_cooldown'])
            
            return JsonResponse({'success': True, 'message': 'Configuration updated'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@login_required
def monitoring_widget(request):
    """Small monitoring widget for dashboard"""
    try:
        system_health = get_system_health()
        database_health = get_database_health()
        
        # Simplified data for widget
        widget_data = {
            'system_status': system_health.get('status', 'unknown'),
            'database_status': 'healthy' if database_health.get('healthy', False) else 'unhealthy',
            'cpu_percent': system_health.get('data', {}).get('cpu_percent', 0),
            'memory_percent': system_health.get('data', {}).get('memory_percent', 0),
            'disk_percent': system_health.get('data', {}).get('disk_percent', 0),
            'alerts_count': len(system_health.get('alerts', [])),
        }
        
        return render(request, 'monitoring/widget.html', {
            'widget_data': widget_data,
            'is_staff': request.user.is_staff
        })
        
    except Exception as e:
        return render(request, 'monitoring/widget.html', {
            'error': str(e),
            'is_staff': request.user.is_staff
        })

# Test monitoring endpoints
@staff_member_required
def test_monitoring(request):
    """Test monitoring system"""
    try:
        # Test system health check
        system_health = get_system_health()
        
        # Test database health check
        database_health = get_database_health()
        
        results = {
            'system_health': system_health,
            'database_health': database_health,
            'timestamp': timezone.now(),
            'background_jobs_available': BACKGROUND_JOBS_AVAILABLE
        }
        
        # Test job scheduling if available
        if BACKGROUND_JOBS_AVAILABLE:
            from .background_jobs import schedule_job, cleanup_cache
            test_job = schedule_job('test_job', cleanup_cache, priority=1)
            results['test_job'] = test_job.to_dict()
        
        return JsonResponse(results, encoder=DjangoJSONEncoder)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Legacy monitoring views (compatibility)
