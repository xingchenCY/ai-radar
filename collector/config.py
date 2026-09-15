from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .models import SourceConfig


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "collector" / "sources.yaml"


def load_config(path: str | Path = DEFAULT_CONFIG) -> tuple[list[SourceConfig], dict[str, list[str]]]:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    sources = [SourceConfig(**item) for item in raw.get("sources", [])]
    topic_queries = raw.get("topic_queries", {})
    return sources, topic_queries


def load_snapshot(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def write_json_atomic(path: str | Path, value: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    json.loads(temp.read_text(encoding="utf-8"))
    temp.replace(target)

