from celery import Celery

celery = Celery("tasks",
                broker = "redis://localhost:6379/0",
                backend = "redis://localhost:6379/0"
        )

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

celery.autodiscover_tasks(["tasks"])

import tasks.listings_task.upload_shiksha_task