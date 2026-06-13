"""Resilient HTTP session factory for GitHub API access."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#: Status codes that warrant an automatic retry.
_RETRY_STATUS_CODES = (403, 429, 500, 502, 503)

#: Default retry policy: 5 attempts with exponential back-off (1s, 2s, 4s ...).
_DEFAULT_RETRY = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=list(_RETRY_STATUS_CODES),
    raise_on_status=False,
)


def build_session(retry: Retry | None = None) -> requests.Session:
    """Create a :class:`requests.Session` with automatic retry.

    Re-uses TCP connections across requests, which lowers latency and
    avoids the connection-setup storms that trigger GitHub rate-limits.

    Parameters
    ----------
    retry:
        Custom :class:`urllib3.util.retry.Retry` policy.  Falls back to
        the module-level ``_DEFAULT_RETRY`` when *None*.
    """
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry or _DEFAULT_RETRY)
    session.mount("https://", adapter)
    return session
