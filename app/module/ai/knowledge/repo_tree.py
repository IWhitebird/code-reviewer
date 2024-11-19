import logging
from typing import List, Optional
from app.module.github.gh_service import GHService
from redis import Redis
import json


class FileNode:
    """Represents a file in the repository"""
    def __init__(self, name: str, blob_url: Optional[str] = None, 
                 sha: Optional[str] = None, size: Optional[int] = None):
        self.name = name
        self.blob_url = blob_url
        self.sha = sha
        self.size = size

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'blob_url': self.blob_url,
            'sha': self.sha,
            'size': self.size,
            'type': 'file'
        }


class FolderTree:
    """Represents a directory in the repository"""
    def __init__(self, name: str, sha: str):
        self.name = name
        self.sha = sha
        self.fileNodes: List[FileNode] = []
        self.folderNodes: List['FolderTree'] = []

    def find_folder(self, folder_name: str) -> Optional['FolderTree']:
        """Find a folder by name in the current folder's children"""
        for folder in self.folderNodes:
            if folder.name == folder_name:
                return folder
        return None

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'sha': self.sha,
            'type': 'folder',
            'files': [file.to_dict() for file in self.fileNodes],
            'folders': [folder.to_dict() for folder in self.folderNodes]
        }


class RepoTree:
    """Manages the entire repository tree structure"""
    def __init__(self, gh: GHService, cache: Redis, repo_url: str):
        self.gh = gh
        self.repo_url = repo_url
        self.cache = cache
        self.root: Optional[FolderTree] = None
        self.create_repo_tree()

    def get_cache_key(self) -> str:
        return f"{self.repo_url}_tree"

    def save_to_cache(self) -> None:
        """Save the tree structure to Redis cache"""
        if self.root:
            tree_dict = self.root.to_dict()
            self.cache.set(self.get_cache_key(), json.dumps(tree_dict))

    def load_from_cache(self) -> Optional[dict]:
        """Load the tree structure from Redis cache"""
        cached_data = self.cache.get(self.get_cache_key())
        if cached_data:
            return json.loads(cached_data)
        return None

    def build_tree_from_dict(self, tree_dict: dict) -> FolderTree:
        """Reconstruct tree structure from dictionary representation"""
        folder = FolderTree(name=tree_dict['name'], sha=tree_dict['sha'])
        
        for file_dict in tree_dict.get('files', []):
            file = FileNode(
                name=file_dict['name'],
                blob_url=file_dict['blob_url'],
                sha=file_dict['sha'],
                size=file_dict['size']
            )
            folder.fileNodes.append(file)
        
        for subfolder_dict in tree_dict.get('folders', []):
            subfolder = self.build_tree_from_dict(subfolder_dict)
            folder.folderNodes.append(subfolder)
        
        return folder

    def create_repo_tree(self) -> None:
        """Create the repository tree structure"""
        # Try loading from cache first
        cached_tree = self.load_from_cache()
        if cached_tree:
            self.root = self.build_tree_from_dict(cached_tree)
            return

        # If not in cache, fetch from GitHub
        repo_structure = self.gh.get_repo_file_structure(self.repo_url)
        self.root = FolderTree(name=self.repo_url, sha=repo_structure.sha)

        for file_entry in repo_structure.tree:
            path_parts = file_entry.path.split("/")
            current_folder = self.root

            # Navigate through the path
            for i, part in enumerate(path_parts[:-1]):
                next_folder = current_folder.find_folder(part)
                if not next_folder:
                    next_folder = FolderTree(name=part, sha=file_entry.sha)
                    current_folder.folderNodes.append(next_folder)
                current_folder = next_folder

            # Handle the last part of the path
            last_part = path_parts[-1]
            if file_entry.type == "blob":
                file_node = FileNode(
                    name=last_part,
                    blob_url=file_entry.url,
                    sha=file_entry.sha,
                    size=file_entry.size
                )
                current_folder.fileNodes.append(file_node)
            elif file_entry.type == "tree":
                folder_node = FolderTree(name=last_part, sha=file_entry.sha)
                current_folder.folderNodes.append(folder_node)

        # Save the newly created tree to cache
        self.save_to_cache()

    def get_tree_readable_for_llm(self) -> str:
        """Convert the tree structure to a string readable by LLM"""
        def _convert_folder(folder: FolderTree, indent: int) -> str:
            result = ""
            for file_node in folder.fileNodes:
                result += f"{' ' * (indent)}-{file_node.name}\n"
            for subfolder in folder.folderNodes:
                result += f"{' ' * (indent)}|{subfolder.name}\n"
                result += _convert_folder(subfolder, indent + 1)
            return result

        return _convert_folder(self.get_tree(), 0)

    def get_file_content(self, file_path: str) -> Optional[str]:
        """Fetch the content of a file in the repository"""
        print(f"Fetching file content for {file_path}")
        path_parts = file_path.split("/")
        current_folder = self.root

        # Navigate through the path
        for _, part in enumerate(path_parts[:-1]):
            next_folder = current_folder.find_folder(part)
            if not next_folder:
                return None
            current_folder = next_folder

        # Handle the last part of the path
        last_part = path_parts[-1]
        for file_node in current_folder.fileNodes:
            if file_node.name == last_part:
                return self.gh.get_file_content(file_node.blob_url)
        return None

    def get_tree(self) -> Optional[FolderTree]:
        """Return the root of the tree structure"""
        return self.root