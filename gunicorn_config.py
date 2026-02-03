"""
Gunicorn Configuration for Production Deployment
Optimized for Oracle Cloud Infrastructure
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "logs/gunicorn_access.log")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "logs/gunicorn_error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "upstox_trading_platform"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# Graceful restart
graceful_timeout = 30


def post_fork(server, worker):
    """Called after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
