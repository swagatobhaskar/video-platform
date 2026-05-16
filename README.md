## Must Additions in the Upload Flow
1. Video chunks uploads are sequential. It has to be made parallel.
2. Pause/Resume uploads.
3. Resume after page refresh.

4. Show seeked thumbnail/preview after upload completion


$ docker run -d --name redis -p 6379:6379 redis

$ docker exec -it redis redis-cli ping
PONG


Run celery with queue name: `celery -A app.celery_worker.celery worker -Q default --loglevel=info`
