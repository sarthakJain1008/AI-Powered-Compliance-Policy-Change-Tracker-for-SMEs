"""Polite HTTP fetcher with retries (stage 1: monitor/fetch)."""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

UA = "Mozilla/5.0 (compatible; ComplianceTrackerBot/0.1; academic project)"


@dataclass
class Fetched:
    status: int
    body: bytes
    final_url: str
    content_type: str = ""


class Fetcher:
    def __init__(self, delay: float = 1.0, retries: int = 3, timeout: int = 40):
        self.delay, self.retries, self.timeout = delay, retries, timeout
        self._last = 0.0

    def get(self, url: str) -> Fetched:
        err: Exception | None = None
        for attempt in range(self.retries):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return Fetched(r.status, r.read(), r.geturl(), r.headers.get("Content-Type", ""))
            except urllib.error.HTTPError as e:
                if e.code < 500 and e.code != 429:      # 4xx is final
                    return Fetched(e.code, b"", url)
                err = e
            except Exception as e:                       # network / timeout: retry with backoff
                err = e
            time.sleep(2 ** attempt)
        raise RuntimeError(f"fetch failed after {self.retries} attempts: {err}")
