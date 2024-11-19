
from pydantic import BaseModel

class RepoMetaRequest(BaseModel):
    repo_url: str

class PRMetaRequest(BaseModel):
    repo_url: str
    pr_number: int

class PRFilesRequest(BaseModel):
    repo_url: str
    pr_number: int