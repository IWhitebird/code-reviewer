import logging
import httpx

class GHService:
    
    @classmethod
    async def get_pr_meta(cls, repo_url: str, pr_number: int, github_token: str):
        logging.info(f"Fetching PR metadata for {repo_url}#{pr_number}")
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        repo_path = repo_url.replace("https://github.com/", "")
        url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch PR metadata: {response.status_code} - {response.text}")
        
    @classmethod
    async def get_pr_files(cls, repo_url: str, pr_number: int, github_token: str):
        logging.info(f"Fetching PR files for {repo_url}#{pr_number}")
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        repo_path = repo_url.replace("https://github.com/", "")
        url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}/files"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch PR files: {response.status_code} - {response.text}")
