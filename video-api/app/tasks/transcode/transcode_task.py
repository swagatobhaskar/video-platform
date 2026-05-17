from app.celery_worker import celery
import time
import asyncio

@celery.task
def process_video_transcoding(key: str):
    
    pass