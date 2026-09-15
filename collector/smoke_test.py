from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .config import load_config
from .fetch import fetch_source
from .parse_feed import parse_entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()
    if not args.real:
        raise SystemExit("Use --real to make network requests")
    sources, _ = load_config()
    checked = []
    for source in sources:
        fetched = fetch_source(source)
        articles, rejected = parse_entries(source, fetched.entries, datetime.now(timezone.utc).isoformat()) if fetched.result.status in {"success", "empty_feed"} else ([], [])
        checked.append({"source_id": source.id, "publisher_id": source.publisher_id, "status": fetched.result.status, "http_status": fetched.result.http_status, "entries": fetched.result.entry_count, "accepted": len(articles), "rejected": len(rejected)})
    publishers = {row["publisher_id"] for row in checked if row["status"] in {"success", "empty_feed"}}
    output = {"checked_at": datetime.now(timezone.utc).isoformat(), "sources": checked, "successful_sources": len(publishers), "meets_minimum": len(publishers) >= 2}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if len(publishers) < 2:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
