from app.module.pr.pr_schema import (
    PRTaskStatus
)

def celery_status_convert(status: str) -> PRTaskStatus:
    if status == 'SUCCESS':
        return PRTaskStatus.completed
    if status == 'FAILURE':
        return PRTaskStatus.failed
    if status in ('PENDING', 'RECEIVED'):
        return PRTaskStatus.pending
    if status in ('STARTED', 'REVOKED'):
        return PRTaskStatus.processing
    return status