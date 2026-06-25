import base64
import logging
import httpx
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.base_url = f"https://api.github.com/repos/{settings.GITHUB_REPO}"

    async def list_markdown_files(self) -> List[Dict[str, str]]:
        """
        Lists all markdown files in the configured OBSIDIAN_SUBFOLDER.
        Returns a list of dicts: [{'name': 'filename.md', 'path': 'fatwas/filename.md', 'download_url': '...'}]
        """
        path = settings.OBSIDIAN_SUBFOLDER.strip("/")
        url = f"{self.base_url}/contents/{path}"
        params = {"ref": settings.GITHUB_BRANCH}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                if response.status_code == 404:
                    logger.warning(f"Subfolder '{path}' not found in repo. It will be created on the first commit.")
                    return []
                
                response.raise_for_status()
                items = response.json()
                
                # If path is a single file instead of folder, wrap in list
                if not isinstance(items, list):
                    items = [items]

                md_files = []
                for item in items:
                    if item.get("type") == "file" and item.get("name", "").endswith(".md"):
                        md_files.append({
                            "name": item["name"],
                            "path": item["path"],
                            "download_url": item["download_url"]
                        })
                return md_files
            except Exception as e:
                logger.error(f"Failed to list files from GitHub: {e}")
                return []

    async def download_file_content(self, download_url: str) -> Optional[str]:
        """
        Downloads raw text content from a given URL.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Use standard Auth header for private repos to pull raw content
                response = await client.get(download_url, headers=self.headers)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(f"Failed to download file from {download_url}: {e}")
                return None

    async def create_or_update_file(self, file_path: str, content: str, commit_message: str) -> bool:
        """
        Creates or updates a file in the GitHub repository.
        file_path: Relative path in the repo, e.g. 'fatwas/my-fatwa.md'
        content: The text content of the markdown file.
        """
        url = f"{self.base_url}/contents/{file_path}"
        
        # Base64 encode content
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        # Check if file exists to get its SHA (needed for updates, though we mostly create)
        sha = None
        async with httpx.AsyncClient() as client:
            try:
                check_res = await client.get(url, headers=self.headers, params={"ref": settings.GITHUB_BRANCH})
                if check_res.status_code == 200:
                    sha = check_res.json().get("sha")
            except Exception:
                pass # If it doesn't exist, we'll get 404 which is fine

            payload = {
                "message": commit_message,
                "content": encoded_content,
                "branch": settings.GITHUB_BRANCH
            }
            if sha:
                payload["sha"] = sha

            try:
                res = await client.put(url, headers=self.headers, json=payload)
                if res.status_code in [200, 201]:
                    logger.info(f"Successfully committed {file_path} to GitHub.")
                    return True
                else:
                    logger.error(f"Failed to commit file. Status: {res.status_code}, Response: {res.text}")
                    return False
            except Exception as e:
                logger.error(f"GitHub commit request exception: {e}")
                return False

github_client = GitHubClient()
