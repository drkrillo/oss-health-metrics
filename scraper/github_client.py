"""Minimal GitHub API client for extracting repository health data."""

from __future__ import annotations

import os
from typing import Any

import requests

from dotenv import load_dotenv
load_dotenv()

class GitHubClient:
    """Thin wrapper around the GitHub REST API with automatic pagination."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.getenv("GITHUB_TOKEN", "")

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _paginate(self, url: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Fetch all pages from a GitHub API endpoint."""
        results: list[dict] = []
        params = params or {}
        params.setdefault("per_page", 100)

        while url:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
            resp.raise_for_status()
            results.extend(resp.json())
            url = resp.links.get("next", {}).get("url")
            params = {}
        return results

    def get_repos(self, owner: str) -> list[dict]:
        """Fetch all public repositories for an organization or user."""
        url = f"{self.API_BASE}/users/{owner}/repos"
        return self._paginate(url, {"type": "public"})

    def get_issues(self, owner: str, repo: str) -> list[dict]:
        """Fetch all issues (open + closed), excluding pull requests."""
        url = f"{self.API_BASE}/repos/{owner}/{repo}/issues"
        raw = self._paginate(url, {"state": "all"})
        return [i for i in raw if "pull_request" not in i]

    def get_pull_requests(self, owner: str, repo: str) -> list[dict]:
        """Fetch all pull requests (open + closed + merged)."""
        url = f"{self.API_BASE}/repos/{owner}/{repo}/pulls"
        return self._paginate(url, {"state": "all"})

    def get_contributors(self, owner: str, repo: str) -> list[dict]:
        """Fetch all contributors with commit counts."""
        url = f"{self.API_BASE}/repos/{owner}/{repo}/contributors"
        return self._paginate(url)