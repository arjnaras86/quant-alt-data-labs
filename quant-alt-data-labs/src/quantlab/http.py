from __future__ import annotations

import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session(user_agent: str, requests_per_second: float = 5.0) -> "RateLimitedSession":
    retry = Retry(
        total=4,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = RateLimitedSession(min_interval=1 / requests_per_second)
    session.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


class RateLimitedSession(requests.Session):
    def __init__(self, min_interval: float) -> None:
        super().__init__()
        self.min_interval = min_interval
        self._last_request = 0.0

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        response = super().request(method, url, timeout=30, **kwargs)
        self._last_request = time.monotonic()
        response.raise_for_status()
        return response
