from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .dates import local_date
from .models import Article, SourceResult, article_from_dict, empty_snapshot
from .plain_text import to_plain_text


def _when(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _within_retention(article: Article, now: datetime) -> bool:
    if article.published_at:
        published = _when(article.published_at)
        if published:
            return published >= now - timedelta(days=30)
    first_seen = _when(article.first_seen_at)
    return bool(first_seen and first_seen >= now - timedelta(days=30))


def _find_existing(articles: dict[str, Article], incoming: Article) -> Article | None:
    for key in incoming.identity_keys:
        for article in articles.values():
            if key in article.identity_keys:
                return article
    return None


def _merge_article(old: Article, new: Article) -> Article:
    old.identity_keys = list(dict.fromkeys(old.identity_keys + new.identity_keys))
    old.last_seen_at = new.last_seen_at
    if new.title and new.title != old.title:
        old.title = new.title
    old_has_promotion = any(marker in old.summary_text for marker in ("欢迎关注", "点击关注"))
    if new.summary_text and (len(new.summary_text) > len(old.summary_text) or old_has_promotion):
        old.summary_text = new.summary_text
    if new.published_at:
        if not old.published_at or new.date_confidence > old.date_confidence:
            if old.published_at and old.published_at != new.published_at:
                old.date_history.append({"value": old.published_at, "confidence": old.date_confidence, "observed_at": new.last_seen_at})
            old.published_at = new.published_at
            old.published_at_raw = new.published_at_raw
            old.date_confidence = new.date_confidence
            old.date_status = new.date_status
        elif old.published_at != new.published_at:
            old.date_history.append({"value": new.published_at, "confidence": new.date_confidence, "observed_at": new.last_seen_at})
    old.relevance_score = max(old.relevance_score, new.relevance_score)
    old.matched_terms = list(dict.fromkeys(old.matched_terms + new.matched_terms))[:8]
    return old


def merge_snapshot(previous: dict[str, Any] | None, incoming: list[Article], source_results: list[SourceResult], now_iso: str) -> dict[str, Any]:
    base = previous.copy() if previous else empty_snapshot(now_iso)
    articles: dict[str, Article] = {str(item["article_id"]): article_from_dict(item) for item in base.get("articles", [])}
    new_count = 0
    updated_count = 0
    for article in incoming:
        existing = _find_existing(articles, article)
        if existing:
            _merge_article(existing, article)
            updated_count += 1
        else:
            articles[article.article_id] = article
            new_count += 1
    now = _when(now_iso) or datetime.now(timezone.utc)
    for article in articles.values():
        # Re-apply bounded text cleanup to historical rows so parser fixes also repair retained data.
        article.summary_text = to_plain_text(article.summary_text)
    retained = [article for article in articles.values() if _within_retention(article, now)]
    retained.sort(key=lambda item: item.published_at or item.first_seen_at or "", reverse=True)
    retained = retained[:1200]
    successful = [result for result in source_results if result.status in {"success", "empty_feed"}]
    failed = [result for result in source_results if result.status not in {"success", "empty_feed"}]
    successful_publishers = {result.publisher_id or result.source_id for result in successful}
    if not successful:
        overall = "failed"
    elif len(successful_publishers) < 2:
        overall = "degraded"
    elif failed:
        overall = "partial_success"
    elif new_count == 0:
        overall = "no_new"
    else:
        overall = "success"
    source_states = []
    old_states = {state.get("source_id"): state for state in base.get("source_states", [])}
    for result in source_results:
        old = old_states.get(result.source_id, {})
        failures = 0 if result.status in {"success", "empty_feed"} else int(old.get("consecutive_failures", 0)) + 1
        source_states.append({**result.to_dict(), "consecutive_failures": failures, "attention_required": failures >= 3, "last_success_at": now_iso if result.status in {"success", "empty_feed"} else old.get("last_success_at")})
    runs = list(base.get("recent_runs", []))
    runs.append({"at": now_iso, "overall_status": overall, "sources": [result.to_dict() for result in source_results]})
    runs = runs[-7:]
    last_success = now_iso if successful else base.get("last_success_at")
    return {
        "schema_version": 1,
        "state_version": now_iso,
        "generated_at": now_iso,
        "timezone": "Asia/Shanghai",
        "last_success_at": last_success,
        "last_attempt_at": now_iso,
        "overall_status": overall,
        "articles": [article.to_dict() for article in retained],
        "source_states": source_states,
        "recent_runs": runs,
        "stats": {"article_count": len(retained), "new_count": new_count, "updated_count": updated_count, "rejected_count": sum(result.rejected_count for result in source_results)},
    }
