from pydantic import BaseModel
from typing import List

class FileIssue(BaseModel):
    type: str
    line: int
    description: str
    suggestion: str

class File(BaseModel):
    name: str
    issues: List[FileIssue]

class Summary(BaseModel):
    total_files: int
    total_issues: int
    critical_issues: int

class PRReview(BaseModel):
    files: List[File]
    summary: Summary