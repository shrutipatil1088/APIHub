import os
import redis
from celery import Celery

# Patch redis-py ConnectionPool to use RESP2 protocol by default.
# This prevents 'unknown command HELLO' error when connecting to Redis < 6.0 / Windows Redis.
_orig_pool_init = redis.ConnectionPool.__init__

# Forces Redis to use RESP2.
def _patched_pool_init(self, *args, **kwargs):
    kwargs.setdefault("protocol", 2)
    _orig_pool_init(self, *args, **kwargs)


redis.ConnectionPool.__init__ = _patched_pool_init

# 1. Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# 2. Create the Celery app instance named 'config'.
app = Celery("config")

# 3. Configure Celery using settings from Django.
# - 'django.conf:settings' tells Celery to use Django's settings.
# - namespace='CELERY' means all Celery-related configuration keys in settings
#   must be prefixed with 'CELERY_' (e.g. CELERY_BROKER_URL, CELERY_RESULT_BACKEND).
app.config_from_object("django.conf:settings", namespace="CELERY")

# 4. Autodiscover tasks from all installed Django apps.
# Celery will search for a 'tasks.py' file in every app listed in INSTALLED_APPS.
# If found, it registers all tasks decorated with: @shared_task
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Optional debug task to verify Celery setup.
    Prints request information when executed.
    """
    print(f"Request: {self.request!r}")
