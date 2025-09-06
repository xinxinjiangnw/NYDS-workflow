from celery import Celery
import os

redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery = Celery('backend', broker=redis_url, backend=redis_url)

# 自动从 tasks 模块加载
celery.autodiscover_tasks(['backend.tasks'])
