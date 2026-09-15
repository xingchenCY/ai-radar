from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from .dates import iso_utc, parse_published
from .identity import article_id, canonical_url, identity_keys
from .models import Article, SourceConfig
from .plain_text import to_plain_text
from .relevance import relevance_score


def _entry_date(entry: dict[str, Any], source: SourceConfig) -> tuple[str | None, str | None, int, str]:
    raw = entry.get("published") or entry.get("pubDate") or entry.get("updated")
    value, confidence, status = parse_published(str(raw) if raw else None, source.default_timezone)
    return value, str(raw) if raw else None, confidence, status


def parse_entries(source: SourceConfig, entries: list[dict[str, Any]], collected_at: str, *, include_unclassified: bool = False) -> tuple[list[Article], list[str]]:
    articles: list[Article] = []
    rejected: list[str] = []
    for index, entry in enumerate(entries):
        title = str(entry.get("title") or "").strip()
        if not title or len(title) > 500:
            rejected.append(f"entry {index}: invalid title")
            continue
        raw_link = str(entry.get("link") or "").strip()
        fallback_link = str(entry.get("id") or entry.get("guid") or "").strip()
        url = canonical_url(raw_link) or canonical_url(fallback_link)
        if raw_link and not url:
            rejected.append(f"entry {index}: invalid url")
            continue
        if url and source.allowed_hosts and (urlsplit(url).hostname or "") not in source.allowed_hosts:
            rejected.append(f"entry {index}: host not allowed")
            continue
        summary = to_plain_text(str(entry.get("summary") or entry.get("description") or ""))
        published_at, published_raw, confidence, date_status = _entry_date(entry, source)
        score, matched_terms, content_status = relevance_score(title, summary, source.mode)
        if content_status == "rejected" and not include_unclassified:
            rejected.append(f"entry {index}: relevance score {score}")
            continue
        keys = identity_keys(
            publisher_id=source.publisher_id,
            url=url,
            guid=str(entry.get("guid") or entry.get("id") or "") or None,
            title=title,
            published_at=published_at,
        )
        if not keys:
            rejected.append(f"entry {index}: no identity")
            continue
        articles.append(Article(
            article_id=article_id(keys[0]),
            identity_keys=keys,
            source_id=source.id,
            publisher_id=source.publisher_id,
            source_name=source.name,
            language=source.language,
            title=title,
            summary_text=summary,
            url=url,
            published_at=published_at,
            published_at_raw=published_raw,
            date_status=date_status,
            date_confidence=confidence,
            first_seen_at=collected_at,
            last_seen_at=collected_at,
            relevance_score=score,
            matched_terms=matched_terms,
            date_history=[] if not published_at else [{"value": published_at, "confidence": confidence, "observed_at": collected_at}],
        ))
    return articles, rejected
