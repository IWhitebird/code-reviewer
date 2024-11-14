from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.module.pr.pr_router import pr_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pr_router)

