import os
from celery import Celery

BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# In local dev/tests (no Redis), set CELERY_TASK_ALWAYS_EAGER=true
ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"

celery = Celery(
    __name__,
    broker=None if ALWAYS_EAGER else BROKER_URL,
    backend=None if ALWAYS_EAGER else BACKEND_URL,
)

celery.conf.task_routes = {
    "app.workers.tasks.import_file": {"queue": "imports"},
}

# Eager mode executes tasks in-process (useful for tests/local without Redis)
if ALWAYS_EAGER:
    celery.conf.task_always_eager = True
    celery.conf.task_eager_propagates = True
