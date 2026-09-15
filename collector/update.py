from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config, load_snapshot, write_json_atomic
from .dates import iso_utc, now_utc
from .fetch import fetch_source
from .merge_snapshot import merge_snapshot
from .models import SourceResult
from .parse_feed import parse_entries


def run_update(output: str | Path, bootstrap: str | Path | None = None, *, previous: str | Path | None = None, include_unclassified: bool = False) -> dict:
    sources, _ = load_config()
    target = Path(output)
    previous_snapshot = load_snapshot(previous) if previous else load_snapshot(target)
    if not previous_snapshot and bootstrap:
        previous_snapshot = load_snapshot(bootstrap)
    collected_at = iso_utc(now_utc())
    all_articles = []
    results: list[SourceResult] = []
    for index, source in enumerate([item for item in sources if item.enabled]):
        if index:
            time.sleep(10)
        fetched = fetch_source(source)
        if fetched.result.status in {"success", "empty_feed"}:
            parsed, rejected = parse_entries(source, fetched.entries, collected_at, include_unclassified=include_unclassified)
            all_articles.extend(parsed)
            fetched.result.accepted_count = len(parsed)
            fetched.result.rejected_count = len(rejected)
            fetched.result.rejected_samples = rejected[:10]
        results.append(fetched.result)
    snapshot = merge_snapshot(previous_snapshot, all_articles, results, collected_at)
    write_json_atomic(target, snapshot)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and merge AI Radar RSS sources")
    parser.add_argument("--output", default="data/snapshot.json")
    parser.add_argument("--bootstrap", default="bootstrap/snapshot.json")
    parser.add_argument("--previous", help="Read an existing snapshot from this path instead of the output path")
    parser.add_argument("--include-unclassified", action="store_true")
    args = parser.parse_args()
    snapshot = run_update(args.output, args.bootstrap, previous=args.previous, include_unclassified=args.include_unclassified)
    print(json.dumps({"status": snapshot["overall_status"], "articles": snapshot["stats"]["article_count"], "new": snapshot["stats"]["new_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
