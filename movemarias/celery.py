"""
Celery configuration for Move Marias
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')

app = Celery('movemarias')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Optional configuration, see the application user guide.
app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
    timezone='America/Sao_Paulo',
    enable_utc=True,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
