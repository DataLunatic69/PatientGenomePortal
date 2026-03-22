import multiprocessing

# ── Server socket ─────────────────────────────────────────────────────────────
bind = "0.0.0.0:8000"
backlog = 2048

# ── Workers ───────────────────────────────────────────────────────────────────
# Use uvicorn worker class for async FastAPI support
worker_class = "uvicorn.workers.UvicornWorker"

# Formula: (2 × CPU cores) + 1 — good default for I/O-bound async apps
workers = (multiprocessing.cpu_count() * 2) + 1

# Threads per worker (uvicorn workers are async — keep at 1)
threads = 1

# ── Timeouts ──────────────────────────────────────────────────────────────────
# AlphaGenome scoring can take several minutes for large files
timeout = 600           # 10 minutes — covers worst-case scoring time
keepalive = 5
graceful_timeout = 30

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"         # stdout
errorlog = "-"          # stderr
loglevel = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = "patientgenomeportal"

# ── Security ──────────────────────────────────────────────────────────────────
limit_request_line = 8192
limit_request_fields = 100
limit_request_field_size = 8192