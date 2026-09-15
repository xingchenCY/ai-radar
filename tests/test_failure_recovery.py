from __future__ import annotations

from email.message import Message
from urllib.error import HTTPError
from pathlib import Path

import collector.fetch as fetch_module
import collector.update as update_module
from collector.fetch import _retry_after, fetch_source
from collector.models import SourceConfig, SourceResult
from collector.fetch import FetchOutput


def test_retry_after_supports_seconds_and_http_date() -> None:
    seconds = HTTPError("https://example.com", 429, "limited", Message(), None)
    seconds.headers["Retry-After"] = "7"
    assert _retry_after(seconds) == 7
    date = HTTPError("https://example.com", 429, "limited", Message(), None)
    date.headers["Retry-After"] = "Tue, 15 Sep 2026 00:00:12 GMT"
    date.headers["Date"] = "Tue, 15 Sep 2026 00:00:00 GMT"
    assert _retry_after(date) == 12


class _Response:
    status = 200

    def __init__(self, body: bytes) -> None:
        self.headers = {"Content-Type": "application/rss+xml"}
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self) -> str:
        return "https://example.com/feed.xml"

    def read(self) -> bytes:
        return self.body


def test_503_retries_then_parses(monkeypatch, ai_source) -> None:
    headers = Message()
    temporary = HTTPError(ai_source.feed_url, 503, "temporary", headers, None)
    body = (Path(__file__).resolve().parents[1] / "fixtures" / "normal.xml").read_bytes()
    calls = iter([temporary, _Response(body)])
    def fake_urlopen(*args, **kwargs):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value
    monkeypatch.setattr(fetch_module, "urlopen", fake_urlopen)
    sleeps: list[int] = []
    monkeypatch.setattr(fetch_module.time, "sleep", lambda seconds: sleeps.append(seconds))
    output = fetch_source(ai_source)
    assert output.result.status == "success"
    assert output.result.attempts == 2
    assert output.result.entry_count == 1
    assert sleeps == [2]


def test_403_does_not_retry(monkeypatch, ai_source) -> None:
    error = HTTPError(ai_source.feed_url, 403, "forbidden", Message(), None)
    monkeypatch.setattr(fetch_module, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error))
    monkeypatch.setattr(fetch_module.time, "sleep", lambda _: (_ for _ in ()).throw(AssertionError("403 must not sleep")))
    output = fetch_source(ai_source)
    assert output.result.status == "forbidden"
    assert output.result.attempts == 1


def test_run_update_isolates_one_failed_source(monkeypatch, tmp_path) -> None:
    sources = [
        SourceConfig("one", "publisher-one", "One", "en", "https://one.example/feed", "ai_feed", True, "UTC", ["one.example"]),
        SourceConfig("two", "publisher-two", "Two", "en", "https://two.example/feed", "ai_feed", True, "UTC", ["two.example"]),
        SourceConfig("three", "publisher-three", "Three", "en", "https://three.example/feed", "ai_feed", True, "UTC", ["three.example"]),
    ]
    monkeypatch.setattr(update_module, "load_config", lambda: (sources, {}))
    monkeypatch.setattr(update_module.time, "sleep", lambda _: None)

    def fake_fetch(source: SourceConfig) -> FetchOutput:
        if source.id == "two":
            return FetchOutput(source, SourceResult(source.id, "forbidden", source.publisher_id, source_name=source.name), [])
        return FetchOutput(
            source,
            SourceResult(source.id, "success", source.publisher_id, source_name=source.name, entry_count=1),
            [{"title": f"{source.name} AI update", "link": f"https://{source.id}.example/story", "published": "2026-09-15T00:00:00Z"}],
        )

    monkeypatch.setattr(update_module, "fetch_source", fake_fetch)
    snapshot = update_module.run_update(tmp_path / "snapshot.json")
    assert snapshot["overall_status"] == "partial_success"
    assert {item["source_id"] for item in snapshot["articles"]} == {"one", "three"}
    assert any(item["source_id"] == "two" and item["status"] == "forbidden" for item in snapshot["source_states"])
