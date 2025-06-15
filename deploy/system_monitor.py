#!/usr/bin/env python3
"""
Move Marias - Health Check and Monitoring Script
Comprehensive system monitoring for production environment
"""

import os
import sys
import json
import psutil
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = Path('/var/log/movemarias')
ALERT_THRESHOLDS = {
    'cpu_percent': 80,
    'memory_percent': 85,
    'disk_percent': 90,
    'response_time': 5.0,  # seconds
    'load_average': 2.0,
}

def log_message(level, message, log_file='monitoring.log'):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {level.upper()}: {message}\n"
    
    log_path = LOG_DIR / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(log_entry)
    
    if level in ['ERROR', 'CRITICAL']:
        print(f"🚨 {log_entry.strip()}")
    elif level == 'WARNING':
        print(f"⚠️  {log_entry.strip()}")
    else:
        print(f"ℹ️  {log_entry.strip()}")

def check_system_resources():
    """Monitor system resources"""
    alerts = []
    
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > ALERT_THRESHOLDS['cpu_percent']:
        alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
    
    # Memory Usage
    memory = psutil.virtual_memory()
    if memory.percent > ALERT_THRESHOLDS['memory_percent']:
        alerts.append(f"High memory usage: {memory.percent:.1f}%")
    
    # Disk Usage
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    if disk_percent > ALERT_THRESHOLDS['disk_percent']:
        alerts.append(f"High disk usage: {disk_percent:.1f}%")
    
    # Load Average
    load_avg = os.getloadavg()[0]
    if load_avg > ALERT_THRESHOLDS['load_average']:
        alerts.append(f"High load average: {load_avg:.2f}")
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk_percent,
        'load_average': load_avg,
        'alerts': alerts
    }

def check_django_health():
    """Check Django application health"""
    try:
        start_time = datetime.now()
        response = requests.get('http://localhost:8000/health/', timeout=10)
        response_time = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            status = 'healthy'
            if response_time > ALERT_THRESHOLDS['response_time']:
                alert = f"Slow response time: {response_time:.2f}s"
                log_message('WARNING', alert)
        else:
            status = 'unhealthy'
            log_message('ERROR', f"Health check failed: HTTP {response.status_code}")
        
        return {
            'status': status,
            'response_time': response_time,
            'status_code': response.status_code
        }
    
    except requests.RequestException as e:
        log_message('ERROR', f"Health check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def check_database_connection():
    """Check database connectivity"""
    try:
        # Run Django management command to check DB
        result = subprocess.run([
            sys.executable, str(BASE_DIR / 'manage.py'), 'check', '--database', 'default'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {'status': 'connected'}
        else:
            log_message('ERROR', f"Database check failed: {result.stderr}")
            return {'status': 'error', 'error': result.stderr}
    
    except subprocess.TimeoutExpired:
        log_message('ERROR', "Database check timed out")
        return {'status': 'timeout'}
    except Exception as e:
        log_message('ERROR', f"Database check error: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def check_redis_connection():
    """Check Redis connectivity"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
        r.ping()
        return {'status': 'connected'}
    except Exception as e:
        log_message('WARNING', f"Redis check failed: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def check_ssl_certificate():
    """Check SSL certificate expiration"""
    try:
        result = subprocess.run([
            'openssl', 's_client', '-connect', 'localhost:443', '-servername', 'localhost'
        ], input='', capture_output=True, text=True, timeout=10)
        
        if 'verify return:1' in result.stdout:
            return {'status': 'valid'}
        else:
            return {'status': 'invalid'}
    except Exception as e:
        return {'status': 'unknown', 'error': str(e)}

def check_log_files():
    """Check for recent errors in log files"""
    error_patterns = ['ERROR', 'CRITICAL', 'FATAL', 'Exception']
    recent_errors = []
    
    # Check last 100 lines of main log file
    try:
        log_file = LOG_DIR / 'django.log'
        if log_file.exists():
            result = subprocess.run([
                'tail', '-100', str(log_file)
            ], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if any(pattern in line for pattern in error_patterns):
                    recent_errors.append(line.strip())
    except Exception as e:
        log_message('WARNING', f"Log check failed: {str(e)}")
    
    return {'recent_errors': recent_errors[-10:]}  # Last 10 errors

def send_alert(message, severity='warning'):
    """Send alert notification"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Log the alert
    log_message(severity.upper(), message, 'alerts.log')
    
    # In production, you could send to Slack, email, etc.
    # For now, just write to alerts file
    alert_data = {
        'timestamp': timestamp,
        'severity': severity,
        'message': message
    }
    
    alerts_file = LOG_DIR / 'current_alerts.json'
    
    # Load existing alerts
    try:
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        alerts = []
    
    # Add new alert
    alerts.append(alert_data)
    
    # Keep only last 50 alerts
    alerts = alerts[-50:]
    
    # Save alerts
    with open(alerts_file, 'w') as f:
        json.dump(alerts, f, indent=2)

def main():
    """Main monitoring function"""
    print(f"🔍 Move Marias System Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # System Resources
    resources = check_system_resources()
    print(f"💻 CPU: {resources['cpu_percent']:.1f}% | "
          f"RAM: {resources['memory_percent']:.1f}% | "
          f"Disk: {resources['disk_percent']:.1f}% | "
          f"Load: {resources['load_average']:.2f}")
    
    # Django Health
    django_health = check_django_health()
    print(f"🐍 Django: {django_health['status']} | "
          f"Response: {django_health.get('response_time', 'N/A'):.2f}s")
    
    # Database
    db_status = check_database_connection()
    print(f"🗄️  Database: {db_status['status']}")
    
    # Redis
    redis_status = check_redis_connection()
    print(f"📦 Redis: {redis_status['status']}")
    
    # SSL
    ssl_status = check_ssl_certificate()
    print(f"🔒 SSL: {ssl_status['status']}")
    
    # Check for alerts
    all_alerts = resources['alerts']
    
    if django_health['status'] != 'healthy':
        all_alerts.append(f"Django unhealthy: {django_health.get('error', 'Unknown')}")
    
    if db_status['status'] != 'connected':
        all_alerts.append(f"Database connection failed: {db_status.get('error', 'Unknown')}")
    
    # Send alerts if any
    for alert in all_alerts:
        send_alert(alert, 'warning')
    
    # Log errors
    log_errors = check_log_files()
    if log_errors['recent_errors']:
        log_message('INFO', f"Found {len(log_errors['recent_errors'])} recent errors")
    
    # Summary
    if all_alerts:
        print(f"\n⚠️  Active Alerts: {len(all_alerts)}")
        for alert in all_alerts:
            print(f"   • {alert}")
    else:
        print("\n✅ All systems operational")
    
    print("=" * 60)
    
    # Save status report
    status_report = {
        'timestamp': datetime.now().isoformat(),
        'resources': resources,
        'django': django_health,
        'database': db_status,
        'redis': redis_status,
        'ssl': ssl_status,
        'alerts': all_alerts
    }
    
    status_file = LOG_DIR / 'system_status.json'
    with open(status_file, 'w') as f:
        json.dump(status_report, f, indent=2)

if __name__ == '__main__':
    main()
