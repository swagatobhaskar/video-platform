from celery import Celery

# broker = message queue
# backend = stores task results

celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    # broker="redis://redis:6379/0",  # when using docker-compose
    # backend="redis://redis:6379/0",
    include=["app.tasks.sample_task"],
)

celery.conf.task_routes = {
    "app.tasks.*": {"queue": "default"}
}

#  Example
# celery.conf.task_routes = {
#     "app.tasks.email_*": {"queue": "emails"},
#     "app.tasks.ai_*": {"queue": "ai"},
# }

# This tells Celery to look for 'tasks.py' inside the 'app' module
# celery_app.autodiscover_tasks(["app.tasks"], force=True)

celery.conf.update(
    task_track_started=True,
    result_expires=3600,
)