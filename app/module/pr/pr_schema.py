from enum import Enum
from pydantic import BaseModel
from typing import List, Optional , Any

from app.module.pr.py_model import File, PRReview, Summary

class PRTaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class AnalyzePRRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: Optional[str] = None 
    
class AnalyzePRResponse(BaseModel):
    task_id: str
    
    
class AnalyzePRStatus(BaseModel):
    status: PRTaskStatus
    
#TODO: Remove Any
class AnalyzePRResults(BaseModel):
    task_id: str
    status: PRTaskStatus
    results: Any


"""Input / OutPut of LangChain LLM API"""

class PRAnalyzeLLMInput(BaseModel):
    query: str
    pr_title: str
    file_name: str
    file_content: str
    
class PRAnalyzeLLMOutput(BaseModel):
    file: File
    summary: Summary



