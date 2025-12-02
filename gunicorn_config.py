"""
Gunicorn configuration for production deployment
https://docs.gunicorn.org/en/stable/settings.html
"""
import multiprocessing
import os

# Server socket
bind = '0.0.0.0:8000'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'guest_tracker'

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Reload workers when code changes (development only)
reload = os.getenv('DEBUG', 'False') == 'True'
reload_engine = 'auto'

# Preload app for memory efficiency
preload_app = True

# Maximum requests per worker before restart (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50
