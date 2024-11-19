import base64
import json
import httpx
import os
import logging
from typing import Optional
from github import Github
from github import Auth

from dotenv import load_dotenv

load_dotenv()

class GHService:
    def __init__(self , gh_token : Optional[str] = None):
        if not gh_token:
            gh_token = os.getenv("GH_TOKEN_TEST")
        self.client = Github(auth=Auth.Token(gh_token))
            
    def get_repo_meta(self, repo_url: str):
        """Fetch metadata for a repository."""
        # return self.get_repo_file_structure
        logging.info(f"Fetching repo metadata for {repo_url}")
        repo_path = repo_url.replace("https://github.com/", "")
        try:
            repo = self.client.get_repo(repo_path)
            return repo
        except Exception as e:
            logging.error(f"Failed to fetch repo metadata: {e}")
            raise
    
    def get_repo_file_structure(self, repo_url: str):
        """Fetch file structure for a repository."""
        logging.info(f"Fetching file structure for {repo_url}")
        repo_path = repo_url.replace("https://github.com/", "")
        try:
            repo = self.client.get_repo(repo_path)
            tree = repo.get_git_tree(sha=repo.default_branch, recursive=True)
            return tree
        except Exception as e:
            logging.error(f"Failed to fetch file structure: {e}")
            raise
    
    def get_pr_meta(self, repo_url: str, pr_number: int):
        """Fetch metadata for a pull request."""
        logging.info(f"Fetching PR metadata for {repo_url}#{pr_number}")
        repo_path = repo_url.replace("https://github.com/", "")
        try:
            repo = self.client.get_repo(repo_path)
            pr = repo.get_pull(pr_number)
            return pr
        except Exception as e:
            logging.error(f"Failed to fetch PR metadata: {e}")
            raise

    def get_pr_files(self, repo_url: str, pr_number: int):
        """Fetch files changed in a pull request."""
        logging.info(f"Fetching PR files for {repo_url}#{pr_number}")
        repo_path = repo_url.replace("https://github.com/", "")
        try:
            repo = self.client.get_repo(repo_path)
            pr = repo.get_pull(pr_number)
            return pr
        except Exception as e:
            logging.error(f"Failed to fetch PR files: {e}")
            raise
    
    def get_file_content(self, file_blob_url : str):
        """Fetch data for a file."""
        logging.info(f"Fetching file data for {file_blob_url}")
        try:
            file_base64 = httpx.get(file_blob_url).json()
            file_content_base64 = file_base64["content"]
            file_content_decoded = base64.b64decode(file_content_base64).decode('utf-8')
            return file_content_decoded
        except Exception as e:
            logging.error(f"Failed to fetch file data: {e}")
            return None