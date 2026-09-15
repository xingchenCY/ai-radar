from collector.parse_feed import parse_entries


def test_invalid_url_is_rejected(ai_source) -> None:
    entries, rejected = parse_entries(ai_source, [{"title": "Valid title", "link": "javascript:alert(1)"}], "2026-09-15T00:00:00Z")
    assert entries == []
    assert any("invalid url" in item for item in rejected)


def test_missing_url_and_guid_can_use_title_identity(ai_source) -> None:
    entries, rejected = parse_entries(ai_source, [{"title": "Title-only identity"}], "2026-09-15T00:00:00Z")
    assert not rejected
    assert len(entries) == 1
    assert entries[0].url == ""
    assert entries[0].identity_keys[0].startswith("title:")


def test_include_unclassified_is_a_debug_escape_hatch(broad_source) -> None:
    entry = {"title": "AI 手机摄影体验", "link": "https://example.cn/a", "description": "AI 修图"}
    filtered, rejected = parse_entries(broad_source, [entry], "2026-09-15T00:00:00Z")
    included, _ = parse_entries(broad_source, [entry], "2026-09-15T00:00:00Z", include_unclassified=True)
    assert filtered == [] and rejected
    assert len(included) == 1
