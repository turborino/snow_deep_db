# Gunicorn configuration file for Snow Deep DB Production
# AWS EC2 + ALB Environment

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # 推奨フォーミュラ
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers periodically to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Preload application for better performance
preload_app = True

# Process naming
proc_name = 'snow_deep_gunicorn'

# User and group
user = "ec2-user"
group = "ec2-user"

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process IDs
pidfile = "/var/run/gunicorn/snow_deep.pid"

# Server mechanics
daemon = False
tmp_upload_dir = None

# SSL (handled by ALB, but keeping for reference)
# keyfile = None
# certfile = None

# Environment variables
raw_env = [
    f'DJANGO_SETTINGS_MODULE=snow_predict.settings_production',
]

# Hook functions
def when_ready(server):
    server.log.info("Snow Deep DB server is ready. Listening on: %s", server.address)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

