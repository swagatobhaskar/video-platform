from app.celery_worker import celery
import time
import asyncio

@celery.task
def inititate_transcoding(video_url: str):
    
    pass