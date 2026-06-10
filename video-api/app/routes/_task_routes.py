from fastapi import APIRouter
from celery.result import AsyncResult

from app.celery_worker import celery
from app.tasks._sample_task import long_task

router = APIRouter(prefix="/api/task", tags=["tasks"])

@router.post('/start')
def start_task(name: str):
    task = long_task.delay(name) #type: ignore
    
    return {
        "task_id": task.id,
        "status": "processing"
    }
    
@router.get('/{task_id}')
def get_task(task_id: str):
    # task_result = long_task.AsyncResult(task_id)
    task_result = AsyncResult(task_id, app=celery)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }


