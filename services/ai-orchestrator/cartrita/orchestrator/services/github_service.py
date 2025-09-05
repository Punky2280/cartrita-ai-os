# Cartrita AI OS - GitHub Service
# GitHub integration for repository operations and code analysis

"""
GitHub service for Cartrita AI OS.
Handles repository operations, code search, and GitHub API interactions.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx
import structlog

from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class GitHubService:
    """GitHub service for repository operations and code analysis."""

    def __init__(self):
        """Initialize GitHub service."""
        self.api_key = settings.ai.github_api_key.get_secret_value()
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Cartrita-AI-OS/1.0"
        }

        logger.info("GitHub service initialized")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to GitHub API."""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("GitHub API error", status_code=e.response.status_code, response=e.response.text)
                raise
            except Exception as e:
                logger.error("GitHub request failed", error=str(e))
                raise

    async def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for repositories on GitHub.

        Args:
            query: Search query
            language: Programming language filter
            sort: Sort criteria (stars, forks, updated)
            order: Sort order (asc, desc)
            max_results: Maximum number of results

        Returns:
            List of repository information
        """
        try:
            # Build search query
            search_query = query
            if language:
                search_query += f" language:{language}"

            params = {
                "q": search_query,
                "sort": sort,
                "order": order,
                "per_page": min(max_results, 100)
            }

            logger.info("Searching repositories", query=search_query, sort=sort, order=order)

            response = await self._make_request("GET", "/search/repositories", params=params)

            results = []
            for repo in response.get("items", [])[:max_results]:
                results.append({
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "clone_url": repo["clone_url"],
                    "language": repo["language"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "issues": repo["open_issues_count"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "owner": {
                        "login": repo["owner"]["login"],
                        "url": repo["owner"]["html_url"],
                        "type": repo["owner"]["type"]
                    },
                    "topics": repo.get("topics", [])
                })

            logger.info("Repository search completed", query=search_query, results_count=len(results))
            return results

        except Exception as e:
            logger.error("Repository search failed", query=query, error=str(e))
            return []

    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        repo: Optional[str] = None,
        filename: Optional[str] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for code on GitHub.

        Args:
            query: Code search query
            language: Programming language filter
            repo: Repository filter (owner/repo format)
            filename: Filename filter
            max_results: Maximum number of results

        Returns:
            List of code search results
        """
        try:
            # Build search query
            search_query = query
            if language:
                search_query += f" language:{language}"
            if repo:
                search_query += f" repo:{repo}"
            if filename:
                search_query += f" filename:{filename}"

            params = {
                "q": search_query,
                "per_page": min(max_results, 100)
            }

            logger.info("Searching code", query=search_query)

            response = await self._make_request("GET", "/search/code", params=params)

            results = []
            for result in response.get("items", [])[:max_results]:
                results.append({
                    "name": result["name"],
                    "path": result["path"],
                    "url": result["html_url"],
                    "repository": {
                        "name": result["repository"]["name"],
                        "full_name": result["repository"]["full_name"],
                        "url": result["repository"]["html_url"],
                        "owner": result["repository"]["owner"]["login"]
                    },
                    "score": result.get("score", 0),
                    "text_matches": result.get("text_matches", [])
                })

            logger.info("Code search completed", query=search_query, results_count=len(results))
            return results

        except Exception as e:
            logger.error("Code search failed", query=query, error=str(e))
            return []

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information
        """
        try:
            response = await self._make_request("GET", f"/repos/{owner}/{repo}")

            return {
                "id": response["id"],
                "name": response["name"],
                "full_name": response["full_name"],
                "description": response["description"],
                "url": response["html_url"],
                "clone_url": response["clone_url"],
                "language": response["language"],
                "stars": response["stargazers_count"],
                "forks": response["forks_count"],
                "issues": response["open_issues_count"],
                "created_at": response["created_at"],
                "updated_at": response["updated_at"],
                "pushed_at": response["pushed_at"],
                "size": response["size"],
                "topics": response.get("topics", []),
                "license": response.get("license", {}).get("name") if response.get("license") else None,
                "owner": {
                    "login": response["owner"]["login"],
                    "url": response["owner"]["html_url"],
                    "type": response["owner"]["type"]
                }
            }

        except Exception as e:
            logger.error("Failed to get repository info", owner=owner, repo=repo, error=str(e))
            raise

    async def get_repository_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: str = "main"
    ) -> List[Dict[str, Any]]:
        """
        Get contents of a repository path.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path within repository
            ref: Branch/tag/commit reference

        Returns:
            List of files and directories
        """
        try:
            params = {"ref": ref} if ref != "main" else None
            response = await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)

            results = []
            # Handle both single file and directory listing
            if isinstance(response, list):
                for item in response:
                    results.append({
                        "name": item["name"],
                        "path": item["path"],
                        "type": item["type"],
                        "size": item["size"],
                        "url": item["html_url"],
                        "download_url": item["download_url"],
                        "sha": item["sha"]
                    })
            else:
                # Single file
                results.append({
                    "name": response["name"],
                    "path": response["path"],
                    "type": response["type"],
                    "size": response["size"],
                    "url": response["html_url"],
                    "download_url": response["download_url"],
                    "sha": response["sha"]
                })

            logger.info("Repository contents retrieved", owner=owner, repo=repo, path=path, items=len(results))
            return results

        except Exception as e:
            logger.error("Failed to get repository contents", owner=owner, repo=repo, path=path, error=str(e))
            return []

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str = "main"
    ) -> Dict[str, Any]:
        """
        Get content of a specific file.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Branch/tag/commit reference

        Returns:
            File content information
        """
        try:
            params = {"ref": ref} if ref != "main" else None
            response = await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)

            # Decode content if it's base64 encoded
            import base64
            content = response.get("content", "")
            if response.get("encoding") == "base64":
                content = base64.b64decode(content).decode('utf-8')

            return {
                "name": response["name"],
                "path": response["path"],
                "type": response["type"],
                "size": response["size"],
                "url": response["html_url"],
                "download_url": response["download_url"],
                "sha": response["sha"],
                "content": content,
                "encoding": response.get("encoding", "utf-8")
            }

        except Exception as e:
            logger.error("Failed to get file content", owner=owner, repo=repo, path=path, error=str(e))
            raise

    async def get_repository_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get issues from a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            labels: List of label names to filter by
            max_results: Maximum number of results

        Returns:
            List of issues
        """
        try:
            params = {
                "state": state,
                "per_page": min(max_results, 100)
            }
            if labels:
                params["labels"] = ",".join(labels)

            response = await self._make_request("GET", f"/repos/{owner}/{repo}/issues", params=params)

            results = []
            for issue in response[:max_results]:
                results.append({
                    "id": issue["id"],
                    "number": issue["number"],
                    "title": issue["title"],
                    "body": issue["body"],
                    "url": issue["html_url"],
                    "state": issue["state"],
                    "labels": [{"name": label["name"], "color": label["color"]} for label in issue.get("labels", [])],
                    "assignee": {
                        "login": issue["assignee"]["login"],
                        "url": issue["assignee"]["html_url"]
                    } if issue.get("assignee") else None,
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "comments": issue["comments"],
                    "author": {
                        "login": issue["user"]["login"],
                        "url": issue["user"]["html_url"]
                    }
                })

            logger.info("Repository issues retrieved", owner=owner, repo=repo, state=state, issues_count=len(results))
            return results

        except Exception as e:
            logger.error("Failed to get repository issues", owner=owner, repo=repo, error=str(e))
            return []

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: List of label names

        Returns:
            Created issue information
        """
        try:
            data = {
                "title": title,
                "body": body
            }
            if labels:
                data["labels"] = labels

            response = await self._make_request("POST", f"/repos/{owner}/{repo}/issues", data=data)

            return {
                "id": response["id"],
                "number": response["number"],
                "title": response["title"],
                "url": response["html_url"],
                "state": response["state"],
                "created_at": response["created_at"]
            }

        except Exception as e:
            logger.error("Failed to create issue", owner=owner, repo=repo, title=title, error=str(e))
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check GitHub service health."""
        try:
            # Test API connectivity
            response = await self._make_request("GET", "/rate_limit")
            return {
                "status": "healthy",
                "rate_limit": {
                    "limit": response["rate"]["limit"],
                    "remaining": response["rate"]["remaining"],
                    "reset": response["rate"]["reset"]
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
