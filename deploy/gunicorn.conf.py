# Gunicorn configuration file for Move Marias
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help control memory usage
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/movemarias/gunicorn_access.log"
errorlog = "/var/log/movemarias/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "movemarias"

# Server mechanics
daemon = False
pidfile = "/var/run/movemarias/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Worker tmp directory
worker_tmp_dir = "/dev/shm"

# Preload application for better performance
preload_app = True

# Security
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 8190
