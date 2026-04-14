"""Gunicorn configuration for OpenASBL production."""

bind = "127.0.0.1:8000"
workers = 2
worker_class = "sync"
timeout = 120  # WeasyPrint PDF generation can be slow
accesslog = "/var/log/openasbl/gunicorn-access.log"
errorlog = "/var/log/openasbl/gunicorn-error.log"
loglevel = "info"
