import logging
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
QUEUE_DB = int(os.getenv("QUEUE_DB", 0))
QUEUE_NAME = os.getenv("QUEUE_NAME", "app")

conn_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{QUEUE_DB}"

def create_celery_app() -> Celery:
    celery_app = Celery(QUEUE_NAME, broker=conn_url, backend=conn_url)
    celery_app.autodiscover_tasks(
        ["app.module.pr.pr_worker"],
        related_name="tasks_analyze_pr"
    )
    try:
        celery_app.backend.client.ping()
        logging.info(f"Connected to Redis at: {conn_url}")
    except Exception as e:
        logging.error(f"Failed to connect to Redis at: {conn_url}. Error: {e}")
        raise e
    return celery_app

celery_app = create_celery_app()
