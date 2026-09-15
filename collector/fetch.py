from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import feedparser

from .models import SourceConfig, SourceResult


RETRYABLE_STATUS = {500, 502, 503, 504}


@dataclass
class FetchOutput:
    source: SourceConfig
    result: SourceResult
    entries: list[dict[str, Any]]


def _retry_after(error: HTTPError) -> int | None:
    value = error.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0, int(value))
    except ValueError:
        try:
            server_date = error.headers.get("Date")
            if not server_date:
                return None
            target = parsedate_to_datetime(value)
            current = parsedate_to_datetime(server_date)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            if current.tzinfo is None:
                current = current.replace(tzinfo=timezone.utc)
            return max(0, int((target - current).total_seconds()))
        except Exception:
            return None


def fetch_source(source: SourceConfig, *, timeout_connect: int = 10, timeout_read: int = 20) -> FetchOutput:
    started = time.monotonic()
    result = SourceResult(source_id=source.id, status="network_error", publisher_id=source.publisher_id, source_name=source.name)
    body = b""
    for attempt in range(1, 4):
        result.attempts = attempt
        request = Request(source.feed_url, headers={
            "User-Agent": "AI-Radar/0.1 (+https://github.com/example/ai-radar)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        })
        try:
            with urlopen(request, timeout=max(timeout_connect, timeout_read)) as response:
                result.http_status = getattr(response, "status", 200)
                result.content_type = response.headers.get("Content-Type")
                result.final_url = response.geturl()
                body = response.read()
            break
        except HTTPError as error:
            result.http_status = error.code
            result.error = str(error)
            if error.code == 429:
                result.status = "rate_limited"
                retry_after = _retry_after(error)
                if retry_after:
                    time.sleep(min(retry_after, 30))
                break
            if error.code == 403:
                result.status = "forbidden"
                break
            if error.code == 404:
                result.status = "not_found"
                break
            if error.code not in RETRYABLE_STATUS:
                result.status = "http_error"
                break
            result.status = "server_error"
        except (TimeoutError, URLError, OSError) as error:
            result.error = str(error)
            result.status = "timeout" if isinstance(error, TimeoutError) or "timed out" in str(error).lower() else "network_error"
        if attempt < 3:
            time.sleep((2, 5, 12)[attempt - 1])
    if not body:
        result.duration_ms = int((time.monotonic() - started) * 1000)
        return FetchOutput(source, result, [])
    try:
        parsed = feedparser.parse(body)
    except Exception as error:
        result.status = "parse_error"
        result.error = str(error)
        result.duration_ms = int((time.monotonic() - started) * 1000)
        return FetchOutput(source, result, [])
    if getattr(parsed, "bozo", False) and not parsed.entries:
        result.status = "parse_error"
        result.error = str(getattr(parsed, "bozo_exception", "invalid feed"))
    else:
        result.status = "empty_feed" if not parsed.entries else "success"
    entries = [dict(entry) for entry in parsed.entries]
    result.entry_count = len(entries)
    result.duration_ms = int((time.monotonic() - started) * 1000)
    return FetchOutput(source, result, entries)
