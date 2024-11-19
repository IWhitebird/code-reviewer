from fastapi import APIRouter
from app.module.github.gh_controller import GHController
from app.module.github.gh_schema import RepoMetaRequest, PRMetaRequest, PRFilesRequest

gh_router = APIRouter(default="github" , tags=["Github"])

@gh_router.post("/repo/meta")
async def get_repo_meta(request: RepoMetaRequest):
    return await GHController.get_repo_meta(request.repo_url)

@gh_router.post("/pr/meta")
async def get_pr_meta(request: PRMetaRequest):
    return await GHController.get_pr_meta(request.repo_url, request.pr_number)

@gh_router.post("/pr/files")
async def get_pr_files(request: PRFilesRequest):
    return await GHController.get_pr_files(request.repo_url, request.pr_number)
