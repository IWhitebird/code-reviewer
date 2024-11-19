from fastapi import APIRouter

from app.module.ai.llm.ollama_llm import OllamaLLM
from app.module.ai.llm.gemini_llm import GeminiLLM

# from app.module.ai.agents.pr_review_agent_0 import PRAgent
# from app.module.ai.agents.pr_review_agent import question
# from app.module.ai.agents.pr_review_agent_2 import run
# from app.module.ai.agents.pr_review_agent_3 import runner

from app.module.ai.agents.pr_agent import PRAgent

from app.module.pr.pr_schema import (
    AnalyzePRRequest,
    AnalyzePRResponse,
    AnalyzePRStatus,
    AnalyzePRResults
)
from app.module.pr.pr_controller import PRController
from app.module.pr.pr_service import PRService

pr_router = APIRouter(default="pr" , tags=["Pull Request"])

# @pr_router.get("/testOlama")
# async def test_olama():
#     ola = OllamaLLM().get_langchain_ollama();
#     return ola.invoke(input="Prime numbers from 0 to 100")

# @pr_router.get("/testGemini")
# async def test_gemini():
#     gem = GeminiLLM()
#     return gem.model.invoke(input="Prime numbers from 0 to 100")

# @pr_router.get("/testAgent")
# async def test_gemini():
#     agent = PRAgent()
#     return agent.run_query("Prime numbers from 0 to 100")


@pr_router.get("/results/{task_id}", response_model=AnalyzePRResults)
async def get_pr_results(task_id: str):
    return PRController.pr_results(task_id=task_id)


@pr_router.get("/status/{task_id}", response_model=AnalyzePRStatus)
async def get_pr_status(task_id: str):
    return PRController.pr_status(task_id=task_id)

@pr_router.post("/analyze-pr", response_model=AnalyzePRResponse)
async def analyze_pr(request: AnalyzePRRequest):
    return PRController.analyze_pr(request=request)
    
@pr_router.post("/analyze-pr-v2")
async def analyze_pr_test(request: AnalyzePRRequest):
    return PRController.analyze_pr_v2(request=request)