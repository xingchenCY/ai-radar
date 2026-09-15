from collector.dates import local_date, parse_published


def test_explicit_offset_has_highest_confidence() -> None:
    value, confidence, status = parse_published("2026-09-14 23:30:00 +0000", "Asia/Shanghai")
    assert value == "2026-09-14T23:30:00Z"
    assert confidence == 3
    assert status == "known"
    assert local_date(value) == "2026-09-15"


def test_default_timezone_is_lower_confidence() -> None:
    value, confidence, status = parse_published("2026-09-14 10:00", "Asia/Shanghai")
    assert value == "2026-09-14T02:00:00Z"
    assert confidence == 1
    assert status == "known"


def test_invalid_or_missing_date_is_unknown() -> None:
    assert parse_published(None, "UTC") == (None, 0, "unknown")
    assert parse_published("not a date", "UTC") == (None, 0, "unknown")
