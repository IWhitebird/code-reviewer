from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.module.github.gh_router import gh_router
from app.module.pr.pr_router import pr_router


app = FastAPI(
    title="Code Reviewer for Pull Requests",
    version="1.0",
    description="This is a simple code reviewer for pull requests using langchain and agents.",
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pr_router)
app.include_router(gh_router)
