from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from .config import load_config
from .fetch import fetch_source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()
    if not args.real:
        raise SystemExit("Use --real to make network requests")
    sources, _ = load_config()
    rows = []
    for source in sources:
        fetched = fetch_source(source)
        rows.append({"source_id": source.id, "name": source.name, "url": source.feed_url, **fetched.result.to_dict()})
        print(f"[{fetched.result.status.upper()}] {source.name}: {fetched.result.http_status or '-'} entries={fetched.result.entry_count}", file=sys.stderr)
    print(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "sources": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
