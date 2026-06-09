"""Extract GitHub data for configured targets and save as CSV."""

from __future__ import annotations

import csv
import os
from pathlib import Path

from github_client import GitHubClient

from dotenv import load_dotenv
load_dotenv()

class GitHubExtractor:
    """Extracts repository data via the GitHub API and saves it as CSV."""

    def __init__(self, client: GitHubClient, output_dir: Path) -> None:
        self._client = client
        self._output_dir = output_dir

    def _write_csv(self, filename: str, rows: list[dict], fields: list[str]) -> None:
        path = self._output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"  {filename}: {len(rows)} rows")

    def extract_issues(self, owner: str, repo: str) -> list[dict]:
        raw = self._client.get_issues(owner, repo)
        return [
            {
                "repo": f"{owner}/{repo}",
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "author": i["user"]["login"],
                "labels": ",".join(l["name"] for l in i["labels"]),
                "comments": i["comments"],
                "created_at": i["created_at"],
                "closed_at": i.get("closed_at"),
                "updated_at": i["updated_at"],
            }
            for i in raw
        ]

    def extract_pull_requests(self, owner: str, repo: str) -> list[dict]:
        raw = self._client.get_pull_requests(owner, repo)
        return [
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
                "additions": pr.get("additions"),
                "deletions": pr.get("deletions"),
            }
            for pr in raw
        ]

    def extract_contributors(self, owner: str, repo: str) -> list[dict]:
        raw = self._client.get_contributors(owner, repo)
        return [
            {
                "repo": f"{owner}/{repo}",
                "login": c["login"],
                "contributions": c["contributions"],
            }
            for c in raw
        ]

    def extract_all(self, targets: list[tuple[str, str]]) -> None:
        """Extract issues, PRs, and contributors for all targets and save as CSV."""
        all_issues: list[dict] = []
        all_prs: list[dict] = []
        all_contributors: list[dict] = []

        for owner, repo in targets:
            print(f"  {owner}/{repo}")
            all_issues.extend(self.extract_issues(owner, repo))
            all_prs.extend(self.extract_pull_requests(owner, repo))
            all_contributors.extend(self.extract_contributors(owner, repo))

        self._write_csv("issues.csv", all_issues,
                        ["repo", "number", "title", "state", "author", "labels",
                         "comments", "created_at", "closed_at", "updated_at"])

        self._write_csv("pull_requests.csv", all_prs,
                        ["repo", "number", "title", "state", "author", "merged_at",
                         "created_at", "closed_at", "updated_at", "additions", "deletions"])

        self._write_csv("contributors.csv", all_contributors,
                        ["repo", "login", "contributions"])


def _resolve_targets(client: GitHubClient) -> list[tuple[str, str]]:
    """Parse GITHUB_TARGETS env var into (owner, repo) tuples.

    Supports two formats separated by commas:
        - "owner/repo"  → single repo
        - "owner"       → all public repos for that org/user
    """
    raw = os.getenv("GITHUB_TARGETS", "drkrillo")
    targets: list[tuple[str, str]] = []

    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if "/" in entry:
            owner, repo = entry.split("/", 1)
            targets.append((owner, repo))
        else:
            repos = client.get_repos(entry)
            print(f"Found {len(repos)} repos in {entry}")
            targets.extend((entry, r["name"]) for r in repos)

    return targets


def main() -> None:
    output_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    client = GitHubClient()
    targets = _resolve_targets(client)
    print(f"Extracting {len(targets)} repos...")

    extractor = GitHubExtractor(client, output_dir)
    extractor.extract_all(targets)
    print("Done.")


if __name__ == "__main__":
    main()