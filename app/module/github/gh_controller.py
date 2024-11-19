import logging
from fastapi import HTTPException
from app.module.github.gh_service import GHService

class GHController:
    @classmethod
    async def get_repo_meta(cls, repo_url: str):
        try:
            logging.info(f"Fetching repository metadata for {repo_url}")
            return await GHService().get_repo_meta(repo_url).raw_data
        except Exception as e:
            logging.error(f"Error in controller while fetching repo metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching repository metadata: {e}")

    @classmethod
    async def get_pr_meta(cls, repo_url: str, pr_number: int):
        try:
            logging.info(f"Fetching PR metadata for {repo_url} PR #{pr_number}")
            return await GHService().get_pr_meta(repo_url, pr_number).raw_data
        except Exception as e:
            logging.error(f"Error in controller while fetching PR metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching PR metadata: {e}")

    @classmethod
    async def get_pr_files(cls, repo_url: str, pr_number: int):
        try:
            logging.info(f"Fetching PR files for {repo_url} PR #{pr_number}")
            return await GHService().get_pr_files(repo_url, pr_number)
        except Exception as e:
            logging.error(f"Error in controller while fetching PR files: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching PR files: {e}")