from fastapi import APIRouter

from app.module.agents.gemini_agent import GeminiAgent
from app.module.pr.pr_schema import (
    AnalyzePRRequest,
    AnalyzePRResponse,
    AnalyzePRStatus,
    AnalyzePRResults
)
from app.module.pr.pr_controller import PRController

pr_router = APIRouter(default="PR")


# @pr_router.get("/gemini_test")
# async def get_pr_results():
#     agent = GeminiAgent()
#     query = "give me prime numbers between 1 to 100"
#     return agent.model.invoke(query)

@pr_router.get("/results/{task_id}", response_model=AnalyzePRResults)
async def get_pr_results(task_id: str):
    return PRController.pr_results(task_id=task_id)


@pr_router.get("/status/{task_id}", response_model=AnalyzePRStatus)
async def get_pr_status(task_id: str):
    return PRController.pr_status(task_id=task_id)

@pr_router.post("/analyze-pr", response_model=AnalyzePRResponse)
async def analyze_pr(request: AnalyzePRRequest):
    return PRController.analyze_pr(request=request)
    