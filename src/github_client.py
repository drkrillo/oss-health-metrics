"""Minimal GitHub API client for extracting repository health data."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from http_client import build_session

logger = logging.getLogger("scraper.github_client")


class GitHubClient:
    """Thin wrapper around the GitHub REST API with automatic pagination.

    Tracks the total number of HTTP requests made so callers can monitor
    API budget consumption via :attr:`request_count`.

    Parameters
    ----------
    token:
        Personal access token.  Falls back to the ``GITHUB_TOKEN``
        environment variable when *None*.
    """

    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.getenv("GITHUB_TOKEN", "")
        self._session = build_session()
        self._headers = self._build_headers()
        self.request_count: int = 0

    def _build_headers(self) -> dict[str, str]:
        """Build request headers once — they never change between calls."""
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    # -- internal helpers ----------------------------------------------------

    def _paginate(self, url: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Fetch all pages from a GitHub API endpoint."""
        results: list[dict] = []
        params = params or {}
        params.setdefault("per_page", 100)

        while url:
            self.request_count += 1
            resp = self._session.get(
                url, headers=self._headers, params=params, timeout=30
            )

            # Respect GitHub rate-limit headers before raising.
            if resp.status_code in (403, 429) and "X-RateLimit-Reset" in resp.headers:
                reset_at = int(resp.headers["X-RateLimit-Reset"])
                wait = max(reset_at - int(time.time()), 1)
                logger.warning("Rate-limited. Waiting %ds for reset...", wait)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            results.extend(data)

            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            logger.debug(
                "[req #%d] %s — %d items (rate-limit remaining: %s)",
                self.request_count,
                url.split("?")[0],
                len(data),
                remaining,
            )

            url = resp.links.get("next", {}).get("url")
            params = {}  # params are baked into the "next" URL

        return results

    # -- public endpoints ----------------------------------------------------

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

    def get_issue_comments(self, owner: str, repo: str) -> list[dict]:
        """Fetch all comments across all issues and PRs in a repo.

        Uses the repo-level endpoint so one paginated call covers every
        issue and pull request.  GitHub treats PRs as issues, so this
        single endpoint returns comments from both.
        """
        url = f"{self.API_BASE}/repos/{owner}/{repo}/issues/comments"
        return self._paginate(url, {"sort": "created", "direction": "asc"})

    def get_forks(self, owner: str, repo: str) -> list[dict]:
        """Fetch all forks with creation timestamps.

        Uses the repo-level endpoint — one paginated call returns every fork.
        """
        url = f"{self.API_BASE}/repos/{owner}/{repo}/forks"
        return self._paginate(url, {"sort": "newest"})

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all review events for a single pull request.

        There is no repo-level endpoint for reviews, so callers must
        iterate over each PR number individually.
        """
        url = f"{self.API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        return self._paginate(url)
