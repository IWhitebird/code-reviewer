import json
import logging
from fastapi import HTTPException
from app.module.pr.pr_helper import celery_status_convert
from app.module.pr.pr_schema import (
    AnalyzePRRequest,
    AnalyzePRResponse,
    AnalyzePRStatus,
    AnalyzePRResults,
)
from app.module.pr.py_model import PRReview
from app.worker.celery_app import celery_app
from app.db.redis_app import redis_app

class PRController:
    @staticmethod
    def pr_results(task_id: str) -> AnalyzePRResults:
        try:
            task = celery_app.AsyncResult(task_id)
            result = None
            if task.status == 'SUCCESS':
                redis_result = redis_app.get(task_id)
                if(redis_result):
                    result = json.loads(redis_result.decode('utf-8'))
            return {"task_id": result["task_id"], "status": celery_status_convert(result["status"]), "results": result["results"]}
        except Exception as e:
            logging.error(f"Unexpected error retrieving task status for task_id={task_id}: {e}")
            raise HTTPException(status_code=404, detail="Result not found")

    @staticmethod
    def pr_status(task_id: str) -> AnalyzePRStatus:
        try:
            task = celery_app.AsyncResult(task_id)
            return {"status": celery_status_convert(task.status)}
        except Exception as e:
            logging.error(f"Unexpected error retrieving task results for task_id={task_id}: {e}")
            raise HTTPException(status_code=404, detail="Task not found")


    @staticmethod
    def analyze_pr(request: AnalyzePRRequest) -> AnalyzePRResponse:
        try:
            task = celery_app.send_task(
                name='tasks_analyze_pr',
                args=[request.repo_url, request.pr_number, request.github_token],
            )
            return {"task_id": task.id}
        except Exception as e:
            logging.error(f"Unexpected error while analyzing PR: {e}")
            raise HTTPException(status_code=500, detail="Failed to analyze PR")
