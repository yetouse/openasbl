"""Gunicorn configuration for OpenASBL production."""

import os

# Le VPS peut héberger plusieurs services : le port est configurable pour
# éviter les collisions entre applications.
bind = os.environ.get("OPENASBL_BIND", "127.0.0.1:8000")
workers = int(os.environ.get("OPENASBL_WORKERS", "2"))
worker_class = "sync"
timeout = 120  # WeasyPrint PDF generation can be slow
accesslog = "/var/log/openasbl/gunicorn-access.log"
errorlog = "/var/log/openasbl/gunicorn-error.log"
loglevel = "info"
