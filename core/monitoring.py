"""
System monitoring and alerting for Move Marias
"""
import os
import time
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.core.cache import cache
from pathlib import Path
import json

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system resources and send alerts"""
    
    def __init__(self):
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time_ms': 2000,
        }
        
        self.alert_cooldown = 300  # 5 minutes between alerts
        self.monitoring_data = []
        
    def check_system_health(self):
        """Check system health and return status"""
        if not PSUTIL_AVAILABLE:
            return {
                'status': 'unknown',
                'data': {},
                'alerts': [],
                'error': 'psutil not available'
            }
        
        try:
            health_data = {
                'timestamp': timezone.now(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': psutil.virtual_memory(),
                'disk': psutil.disk_usage('/'),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                'disk_io': psutil.disk_io_counters(),
                'network_io': psutil.net_io_counters(),
            }
            
            # Convert to serializable format
            serializable_data = {
                'timestamp': health_data['timestamp'].isoformat(),
                'cpu_percent': health_data['cpu_percent'],
                'memory_percent': health_data['memory'].percent,
                'memory_available_gb': round(health_data['memory'].available / (1024**3), 2),
                'disk_percent': round((health_data['disk'].used / health_data['disk'].total) * 100, 2),
                'disk_free_gb': round(health_data['disk'].free / (1024**3), 2),
                'load_average_1m': health_data['load_average'][0],
                'load_average_5m': health_data['load_average'][1],
                'load_average_15m': health_data['load_average'][2],
            }
            
            # Check for alerts
            alerts = self._check_thresholds(serializable_data)
            
            # Store data
            self.monitoring_data.append(serializable_data)
            
            # Keep only last 100 readings
            if len(self.monitoring_data) > 100:
                self.monitoring_data = self.monitoring_data[-100:]
            
            return {
                'status': 'healthy' if not alerts else 'warning',
                'data': serializable_data,
                'alerts': alerts
            }
            
        except ImportError:
            logger.warning("psutil not available for system monitoring")
            return {
                'status': 'unknown',
                'data': {},
                'alerts': [],
                'error': 'psutil not available'
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                'status': 'error',
                'data': {},
                'alerts': [],
                'error': str(e)
            }
    
    def _check_thresholds(self, data):
        """Check if any thresholds are exceeded"""
        alerts = []
        
        # CPU check
        if data['cpu_percent'] > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f"High CPU usage: {data['cpu_percent']:.1f}%",
                'threshold': self.thresholds['cpu_percent'],
                'current': data['cpu_percent']
            })
        
        # Memory check
        if data['memory_percent'] > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f"High memory usage: {data['memory_percent']:.1f}%",
                'threshold': self.thresholds['memory_percent'],
                'current': data['memory_percent']
            })
        
        # Disk check
        if data['disk_percent'] > self.thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f"High disk usage: {data['disk_percent']:.1f}%",
                'threshold': self.thresholds['disk_percent'],
                'current': data['disk_percent']
            })
        
        # Low disk space check (less than 1GB)
        if data['disk_free_gb'] < 1.0:
            alerts.append({
                'type': 'disk_low',
                'severity': 'critical',
                'message': f"Low disk space: {data['disk_free_gb']:.2f}GB free",
                'threshold': 1.0,
                'current': data['disk_free_gb']
            })
        
        return alerts
    
    def send_alert(self, alert):
        """Send alert notification"""
        # Check cooldown
        cache_key = f"alert_cooldown_{alert['type']}"
        if cache.get(cache_key):
            return False  # Still in cooldown
        
        # Set cooldown
        cache.set(cache_key, True, self.alert_cooldown)
        
        # Prepare email
        subject = f"Move Marias Alert: {alert['type'].replace('_', ' ').title()}"
        message = f"""
System Alert Notification

Alert Type: {alert['type']}
Severity: {alert['severity']}
Message: {alert['message']}
Threshold: {alert['threshold']}
Current Value: {alert['current']}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system immediately.

---
Move Marias Monitoring System
        """
        
        # Send to admins
        admin_emails = [email for name, email in getattr(settings, 'ADMINS', [])]
        
        if admin_emails:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=False
                )
                logger.info(f"Alert sent for {alert['type']}: {alert['message']}")
                return True
            except Exception as e:
                logger.error(f"Failed to send alert email: {e}")
                return False
        
        return False
    
    def get_monitoring_data(self, hours=24):
        """Get monitoring data for the last N hours"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Filter data by time
        filtered_data = []
        for data_point in self.monitoring_data:
            data_time = datetime.fromisoformat(data_point['timestamp'].replace('Z', '+00:00'))
            if data_time >= cutoff_time:
                filtered_data.append(data_point)
        
        return filtered_data
    
    def get_system_stats(self):
        """Get current system statistics"""
        if not self.monitoring_data:
            return {}
        
        latest = self.monitoring_data[-1] if self.monitoring_data else {}
        
        # Calculate averages over last 10 readings
        recent_data = self.monitoring_data[-10:] if len(self.monitoring_data) >= 10 else self.monitoring_data
        
        if recent_data:
            avg_cpu = sum(d['cpu_percent'] for d in recent_data) / len(recent_data)
            avg_memory = sum(d['memory_percent'] for d in recent_data) / len(recent_data)
            avg_disk = sum(d['disk_percent'] for d in recent_data) / len(recent_data)
        else:
            avg_cpu = avg_memory = avg_disk = 0
        
        return {
            'current': latest,
            'averages': {
                'cpu_percent': round(avg_cpu, 2),
                'memory_percent': round(avg_memory, 2),
                'disk_percent': round(avg_disk, 2),
            },
            'thresholds': self.thresholds,
            'data_points': len(self.monitoring_data)
        }
    
    def continuous_monitoring(self, interval=60):
        """Run continuous monitoring (for background processes)"""
        logger.info("Starting continuous system monitoring...")
        
        while True:
            try:
                health_status = self.check_system_health()
                
                # Send alerts if needed
                for alert in health_status.get('alerts', []):
                    self.send_alert(alert)
                
                # Log status
                status = health_status['status']
                if status == 'warning':
                    logger.warning(f"System health warning: {len(health_status['alerts'])} alerts")
                elif status == 'error':
                    logger.error(f"System health error: {health_status.get('error', 'Unknown error')}")
                else:
                    logger.debug("System health check completed successfully")
                
                # Save monitoring data periodically
                if len(self.monitoring_data) % 10 == 0:
                    self._save_monitoring_data()
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(interval)
    
    def _save_monitoring_data(self):
        """Save monitoring data to file"""
        try:
            monitoring_file = Path(settings.BASE_DIR) / 'logs' / 'monitoring.json'
            monitoring_file.parent.mkdir(exist_ok=True)
            
            with open(monitoring_file, 'w') as f:
                json.dump(self.monitoring_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")

class DatabaseMonitor:
    """Monitor database performance and health"""
    
    def __init__(self):
        self.query_times = []
        self.slow_query_threshold = 1.0  # seconds
    
    def check_database_health(self):
        """Check database health"""
        try:
            from django.db import connection
            
            start_time = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            query_time = time.time() - start_time
            
            # Store query time
            self.query_times.append(query_time)
            if len(self.query_times) > 100:
                self.query_times = self.query_times[-100:]
            
            # Check if query was slow
            is_slow = query_time > self.slow_query_threshold
            
            return {
                'healthy': result and result[0] == 1,
                'query_time': query_time,
                'slow_query': is_slow,
                'avg_query_time': sum(self.query_times) / len(self.query_times) if self.query_times else 0,
                'max_query_time': max(self.query_times) if self.query_times else 0,
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'query_time': None,
                'slow_query': False,
            }
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            from django.db import connection
            
            # Get database file size for SQLite
            db_config = settings.DATABASES['default']
            if 'sqlite' in db_config['ENGINE']:
                db_path = db_config['NAME']
                if os.path.exists(db_path):
                    db_size = os.path.getsize(db_path)
                    db_size_mb = round(db_size / (1024**2), 2)
                else:
                    db_size_mb = 0
            else:
                db_size_mb = 0  # Would need specific queries for other databases
            
            # Get table count
            with connection.cursor() as cursor:
                if 'sqlite' in db_config['ENGINE']:
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                else:
                    table_count = 0
            
            return {
                'database_size_mb': db_size_mb,
                'table_count': table_count,
                'engine': db_config['ENGINE'],
                'connection_max_age': db_config.get('CONN_MAX_AGE', 0),
                'query_times': {
                    'count': len(self.query_times),
                    'avg': sum(self.query_times) / len(self.query_times) if self.query_times else 0,
                    'max': max(self.query_times) if self.query_times else 0,
                    'min': min(self.query_times) if self.query_times else 0,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'error': str(e)}

# Global instances
system_monitor = SystemMonitor()
database_monitor = DatabaseMonitor()

# Convenience functions
def get_system_health():
    """Get current system health"""
    return system_monitor.check_system_health()

def get_database_health():
    """Get current database health"""
    return database_monitor.check_database_health()

def get_full_system_status():
    """Get comprehensive system status"""
    return {
        'system': get_system_health(),
        'database': get_database_health(),
        'timestamp': timezone.now().isoformat(),
    }
