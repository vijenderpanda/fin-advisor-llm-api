# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8002"
backlog = 2048

# Worker processes
workers = 2  # Start with fewer workers for testing
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "fin_advisor_api"

# Server mechanics
daemon = False
pidfile = "gunicorn.pid"
user = None
group = None
umask = 0
reload = True

# SSL
keyfile = None
certfile = None

def worker_exit(server, worker):
    """Clean up on worker exit."""
    import gc
    gc.collect()