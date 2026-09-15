from __future__ import annotations

from pathlib import Path

import pytest

from collector.models import SourceConfig


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ai_source() -> SourceConfig:
    return SourceConfig(
        id="test-ai",
        publisher_id="publisher-a",
        name="Test AI",
        language="en",
        feed_url="https://example.com/feed.xml",
        mode="ai_feed",
        default_timezone="UTC",
        allowed_hosts=["example.com"],
    )


@pytest.fixture
def broad_source() -> SourceConfig:
    return SourceConfig(
        id="test-broad",
        publisher_id="publisher-b",
        name="Test Broad",
        language="zh",
        feed_url="https://example.cn/feed.xml",
        mode="broad",
        default_timezone="Asia/Shanghai",
        allowed_hosts=["example.cn"],
    )
