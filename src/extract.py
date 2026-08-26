"""Extract GitHub data for configured targets and save as CSV."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path

from github_client import GitHubClient
from log import setup_logging

logger = logging.getLogger("scraper.extract")


class GitHubExtractor:
    """Extracts repository data via the GitHub API and saves it as CSV.

    Each ``extract_*`` method fetches raw API data, flattens it into a
    list of dicts, and returns it.  :meth:`extract_all` orchestrates
    every extractor and writes the combined results to CSV.
    """

    # -- CSV schemas (field order = column order in the file) ----------------

    ISSUES_FIELDS = [
        "repo", "number", "title", "state", "author", "labels",
        "comments", "created_at", "closed_at", "updated_at",
    ]
    PULL_REQUESTS_FIELDS = [
        "repo", "number", "title", "state", "author", "merged_at",
        "created_at", "closed_at", "updated_at",
    ]
    ISSUE_COMMENTS_FIELDS = [
        "repo", "comment_id", "issue_number", "author",
        "author_association", "created_at", "updated_at",
    ]
    PR_REVIEWS_FIELDS = [
        "repo", "pr_number", "review_id", "author",
        "author_association", "state", "submitted_at",
    ]
    FORKS_FIELDS = [
        "repo", "author", "forked_at",
    ]

    def __init__(self, client: GitHubClient, output_dir: Path) -> None:
        self._client = client
        self._output_dir = output_dir

    # -- helpers -------------------------------------------------------------

    def _write_csv(self, filename: str, rows: list[dict], fields: list[str]) -> None:
        path = self._output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        logger.info("Saved %s — %d rows", filename, len(rows))

    def _log_api_calls(self) -> None:
        """Log running total of API requests made so far."""
        logger.info("API requests so far: %d", self._client.request_count)

    # -- extractors ----------------------------------------------------------

    def extract_issues(self, owner: str, repo: str) -> list[dict]:
        logger.info("Extracting issues...")
        raw = self._client.get_issues(owner, repo)
        result = [
            {
                "repo": f"{owner}/{repo}",
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "author": i["user"]["login"],
                "labels": ",".join(label["name"] for label in i["labels"]),
                "comments": i["comments"],
                "created_at": i["created_at"],
                "closed_at": i.get("closed_at"),
                "updated_at": i["updated_at"],
            }
            for i in raw
        ]
        logger.info("  issues: %d extracted", len(result))
        self._log_api_calls()
        return result

    def extract_pull_requests(self, owner: str, repo: str) -> list[dict]:
        logger.info("Extracting pull requests...")
        raw = self._client.get_pull_requests(owner, repo)
        result = [
            {
                "repo": f"{owner}/{repo}",
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "merged_at": pr.get("merged_at"),
                "created_at": pr["created_at"],
                "closed_at": pr.get("closed_at"),
                "updated_at": pr["updated_at"],
            }
            for pr in raw
        ]
        logger.info("  pull_requests: %d extracted", len(result))
        self._log_api_calls()
        return result

    def extract_issue_comments(self, owner: str, repo: str) -> list[dict]:
        """Extract all comments across issues and PRs using the repo-level endpoint."""
        logger.info("Extracting issue comments (repo-level)...")
        raw = self._client.get_issue_comments(owner, repo)
        result = [
            {
                "repo": f"{owner}/{repo}",
                "comment_id": c["id"],
                "issue_number": int(c["issue_url"].rsplit("/", 1)[-1]),
                "author": c["user"]["login"],
                "author_association": c.get("author_association", ""),
                "created_at": c["created_at"],
                "updated_at": c["updated_at"],
            }
            for c in raw
        ]
        logger.info("  issue_comments: %d extracted", len(result))
        self._log_api_calls()
        return result

    def extract_forks(self, owner: str, repo: str) -> list[dict]:
        """Extract all forks with creation timestamps."""
        logger.info("Extracting forks...")
        raw = self._client.get_forks(owner, repo)
        result = [
            {
                "repo": f"{owner}/{repo}",
                "author": f["owner"]["login"],
                "forked_at": f["created_at"],
            }
            for f in raw
            if f.get("owner")
        ]
        logger.info("  forks: %d extracted", len(result))
        self._log_api_calls()
        return result

    def extract_pr_reviews(
        self, owner: str, repo: str, pr_numbers: list[int]
    ) -> list[dict]:
        """Extract review events for every PR in the repo.

        Requires one API call per PR — the most expensive extraction.
        """
        logger.info("Extracting PR reviews for %d PRs...", len(pr_numbers))
        results: list[dict] = []
        for i, number in enumerate(pr_numbers, 1):
            if i % 25 == 0 or i == len(pr_numbers):
                logger.info(
                    "  reviews progress: %d/%d PRs (API calls: %d)",
                    i, len(pr_numbers), self._client.request_count,
                )
            raw = self._client.get_pr_reviews(owner, repo, number)
            results.extend(
                {
                    "repo": f"{owner}/{repo}",
                    "pr_number": number,
                    "review_id": r["id"],
                    "author": r["user"]["login"],
                    "author_association": r.get("author_association", ""),
                    "state": r["state"],
                    "submitted_at": r.get("submitted_at"),
                }
                for r in raw
                if r.get("user")  # skip ghost/deleted users
            )
        logger.info("  pr_reviews: %d extracted", len(results))
        self._log_api_calls()
        return results

    # -- orchestrator --------------------------------------------------------

    def extract_all(self, owner: str, repo: str) -> None:
        """Extract issues, PRs, comments, forks, and reviews for one repository.

        One repository per run, on purpose.  Every mart aggregates over whatever
        lands in the CSVs, so two repositories in the same warehouse would share
        a contributor funnel, a response-time median and a bus factor that
        describe neither of them.
        """
        logger.info("=== %s/%s ===", owner, repo)

        issues = self.extract_issues(owner, repo)
        prs = self.extract_pull_requests(owner, repo)
        comments = self.extract_issue_comments(owner, repo)
        forks = self.extract_forks(owner, repo)
        reviews = self.extract_pr_reviews(owner, repo, [pr["number"] for pr in prs])

        logger.info("=== Saving CSVs ===")
        self._write_csv("issues.csv", issues, self.ISSUES_FIELDS)
        self._write_csv("pull_requests.csv", prs, self.PULL_REQUESTS_FIELDS)
        self._write_csv("issue_comments.csv", comments, self.ISSUE_COMMENTS_FIELDS)
        self._write_csv("pr_reviews.csv", reviews, self.PR_REVIEWS_FIELDS)
        self._write_csv("forks.csv", forks, self.FORKS_FIELDS)

        logger.info("=== Done. Total API requests: %d ===", self._client.request_count)


# -- CLI entrypoint ---------------------------------------------------------


def _resolve_repo() -> tuple[str, str]:
    """Read GITHUB_REPO as a single "owner/repo" pair.

    A dashboard describes one repository.  Accepting a list here would produce
    marts that silently average unrelated projects together, so the shape of the
    input is what enforces it.
    """
    raw = (os.getenv("GITHUB_REPO") or "").strip()
    if not raw:
        raise SystemExit(
            'GITHUB_REPO is not set. Add it to your .env, for example:\n'
            "    GITHUB_REPO=drkrillo/good-first-issues"
        )
    if raw.count("/") != 1 or not all(raw.split("/")):
        raise SystemExit(f'GITHUB_REPO must be "owner/repo", got: {raw!r}')

    owner, repo = raw.split("/")
    return owner, repo


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    setup_logging()

    output_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    client = GitHubClient()

    owner, repo = _resolve_repo()

    extractor = GitHubExtractor(client, output_dir)
    extractor.extract_all(owner, repo)


if __name__ == "__main__":
    main()
