from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceConfig:
    id: str
    publisher_id: str
    name: str
    language: str
    feed_url: str
    mode: str = "ai_feed"
    enabled: bool = True
    default_timezone: str = "UTC"
    allowed_hosts: list[str] = field(default_factory=list)


@dataclass
class SourceResult:
    source_id: str
    status: str
    publisher_id: str | None = None
    source_name: str | None = None
    attempts: int = 0
    http_status: int | None = None
    content_type: str | None = None
    entry_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    error: str | None = None
    final_url: str | None = None
    duration_ms: int = 0
    rejected_samples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Article:
    article_id: str
    identity_keys: list[str]
    source_id: str
    publisher_id: str
    source_name: str
    language: str
    title: str
    summary_text: str
    url: str
    published_at: str | None
    published_at_raw: str | None
    date_status: str
    date_confidence: int
    first_seen_at: str
    last_seen_at: str
    content_status: str = "source_summary"
    relevance_score: int = 0
    matched_terms: list[str] = field(default_factory=list)
    date_history: list[dict[str, Any]] = field(default_factory=list)
    filter_version: str = "1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def article_from_dict(raw: dict[str, Any]) -> Article:
    return Article(
        article_id=str(raw["article_id"]),
        identity_keys=list(raw.get("identity_keys", [])),
        source_id=str(raw["source_id"]),
        publisher_id=str(raw.get("publisher_id", raw["source_id"])),
        source_name=str(raw.get("source_name", raw["source_id"])),
        language=str(raw.get("language", "en")),
        title=str(raw.get("title", "")),
        summary_text=str(raw.get("summary_text", "")),
        url=str(raw.get("url", "")),
        published_at=raw.get("published_at"),
        published_at_raw=raw.get("published_at_raw"),
        date_status=str(raw.get("date_status", "unknown")),
        date_confidence=int(raw.get("date_confidence", 0)),
        first_seen_at=str(raw.get("first_seen_at", raw.get("collected_at", ""))),
        last_seen_at=str(raw.get("last_seen_at", raw.get("collected_at", ""))),
        content_status=str(raw.get("content_status", "source_summary")),
        relevance_score=int(raw.get("relevance_score", 0)),
        matched_terms=list(raw.get("matched_terms", [])),
        date_history=list(raw.get("date_history", [])),
        filter_version=str(raw.get("filter_version", "1")),
    )


def empty_snapshot(now: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "state_version": now,
        "generated_at": now,
        "timezone": "Asia/Shanghai",
        "last_success_at": None,
        "last_attempt_at": now,
        "overall_status": "degraded",
        "articles": [],
        "source_states": [],
        "recent_runs": [],
        "stats": {"article_count": 0, "new_count": 0, "updated_count": 0, "rejected_count": 0},
    }
