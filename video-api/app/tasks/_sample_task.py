from app.celery_worker import celery
import time

@celery.task #(bind=True, max_retries=3)
def long_task(name: str):
    time.sleep(7)
    
    return {
        "status": "completed",
        "message": f"Hello {name}"
    }


# Retry failed tasks
# @celery.task(bind=True, max_retries=3)
# def send_email(self):
#     try:
#         ...
#     except Exception as exc:
#         raise self.retry(exc=exc, countdown=5)