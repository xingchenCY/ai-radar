from collector.merge_snapshot import merge_snapshot
from collector.models import Article, SourceResult


NOW = "2026-09-15T00:00:00Z"


def article(article_id: str, key: str, *, published_at: str | None = "2026-09-14T00:00:00Z", confidence: int = 3) -> Article:
    return Article(
        article_id=article_id,
        identity_keys=[key],
        source_id="source-a",
        publisher_id="publisher-a",
        source_name="Source A",
        language="en",
        title="AI release",
        summary_text="Summary",
        url="https://example.com/a",
        published_at=published_at,
        published_at_raw=published_at,
        date_status="known" if published_at else "unknown",
        date_confidence=confidence,
        first_seen_at=NOW,
        last_seen_at=NOW,
    )


def success(source_id: str, publisher_id: str) -> SourceResult:
    return SourceResult(source_id=source_id, status="success", publisher_id=publisher_id)


def test_duplicate_import_is_idempotent() -> None:
    first = merge_snapshot(None, [article("art_1", "url:1")], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    second = merge_snapshot(first, [article("art_1", "url:1")], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    assert len(second["articles"]) == 1
    assert second["stats"]["new_count"] == 0
    assert second["overall_status"] == "no_new"


def test_higher_confidence_date_can_correct_old_date() -> None:
    old = merge_snapshot(None, [article("art_1", "url:1", published_at="2026-09-14T00:00:00Z", confidence=1)], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    corrected = merge_snapshot(old, [article("art_1", "url:1", published_at="2026-09-13T00:00:00Z", confidence=3)], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    assert corrected["articles"][0]["published_at"] == "2026-09-13T00:00:00Z"
    assert corrected["articles"][0]["date_history"]


def test_all_sources_failed_keeps_old_articles() -> None:
    old = merge_snapshot(None, [article("art_1", "url:1")], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    failed = [SourceResult(source_id="source-a", status="forbidden", publisher_id="publisher-a"), SourceResult(source_id="source-b", status="timeout", publisher_id="publisher-b")]
    current = merge_snapshot(old, [], failed, "2026-09-15T01:00:00Z")
    assert [row["article_id"] for row in current["articles"]] == ["art_1"]
    assert current["overall_status"] == "failed"


def test_distinct_publishers_are_required_for_healthy_status() -> None:
    result = merge_snapshot(None, [article("art_1", "url:1")], [success("source-a", "same"), success("source-b", "same")], NOW)
    assert result["overall_status"] == "degraded"


def test_retention_uses_first_seen_for_unknown_dates() -> None:
    old = article("art_old", "url:old", published_at=None)
    old.first_seen_at = "2026-08-01T00:00:00Z"
    result = merge_snapshot(None, [old], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    assert result["articles"] == []


def test_clean_summary_can_replace_old_promotional_tail() -> None:
    old_article = article("art_1", "url:1")
    old_article.summary_text = "正文摘要\n欢迎关注官方微信公众号"
    old = merge_snapshot(None, [old_article], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    clean = article("art_1", "url:1")
    clean.summary_text = "正文摘要"
    result = merge_snapshot(old, [clean], [success("source-a", "publisher-a"), success("source-b", "publisher-b")], NOW)
    assert result["articles"][0]["summary_text"] == "正文摘要"
