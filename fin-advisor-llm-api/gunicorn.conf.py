# gunicorn.conf.py
import multiprocessing
import os

# Server socket settings
bind = "0.0.0.0:8002"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended number of workers
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Timeout settings
timeout = 120  # 2 minutes max for a request
keepalive = 5   # 5 seconds keepalive
graceful_timeout = 30

# Prevent worker hanging
max_requests = 1000          # Restart workers after this many requests
max_requests_jitter = 50     # Add randomness to max_requests
worker_tmp_dir = "/dev/shm"  # Fast tmp storage

# Log settings
accesslog = "-"              # Log to stdout
errorlog = "-"              # Log to stderr
loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# SSL settings (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

# Development settings
reload = True                # Auto-reload on code changes
reload_extra_files = []      # Additional files to watch

# Process naming
proc_name = "fin_advisor_api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None

# Logging
capture_output = True
enable_stdio_inheritance = True

def on_starting(server):
    """Log when server starts."""
    server.log.info("Starting Fin Advisor API server")

def worker_int(worker):
    """Log worker interruption."""
    worker.log.info("Worker interrupted (SIGINT/SIGQUIT)")

def worker_abort(worker):
    """Log worker abort."""
    worker.log.info("Worker aborted (SIGABRT)")

def worker_exit(server, worker):
    """Clean up on worker exit."""
    from datetime import datetime
    server.log.info(f"Worker exiting (pid: {worker.pid}) at {datetime.now()}")

def post_fork(server, worker):
    """Execute after worker fork."""
    server.log.info(f"Worker forked (pid: {worker.pid})")

def pre_exec(server):
    """Execute before worker processes are forked."""
    server.log.info("Pre-exec hook")

def pre_request(worker, req):
    """Execute before handling request."""
    worker.log.debug(f"Handling request: {req.uri}")

def post_request(worker, req, environ, resp):
    """Execute after handling request."""
    worker.log.debug(f"Completed request: {req.uri} - Status: {resp.status}")

# Error handling
def handle_error(worker, req, client, addr, exc):
    """Handle errors during request processing."""
    worker.log.error(f"Error handling request from {addr}: {exc}")

# Performance tuning
worker_tmp_dir = "/dev/shm"  # Use RAM for temp files
threads = 4                  # Number of threads per worker

# Keep-alive settings
keepalive_timeout = 5       # How long to wait for requests on a Keep-Alive connection
timeout_keep_alive = 5      # How long to wait for requests on a Keep-Alive connection

# Logging configuration
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'generic': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
            'datefmt': '[%Y-%m-%d %H:%M:%S %z]',
            'class': 'logging.Formatter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        }
    }
}

# Clean up on reload
def on_reload(server):
    """Clean up on code reload."""
    server.log.info("Cleaning up on reload")

def when_ready(server):
    """Execute when server is ready to receive requests."""
    server.log.info("Server is ready to receive requests")