from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {"ref", "ref_src", "source", "campaign", "mc_cid", "mc_eid"}


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(value: str) -> str:
    parts = urlsplit((value or "").strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return ""
    query = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True) if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS]
    hostname = (parts.hostname or "").lower()
    port = parts.port
    netloc = hostname
    if port and not ((parts.scheme.lower() == "http" and port == 80) or (parts.scheme.lower() == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, urlencode(query), ""))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def identity_keys(*, publisher_id: str, url: str, guid: str | None, title: str, published_at: str | None) -> list[str]:
    keys: list[str] = []
    normalized_url = canonical_url(url)
    if normalized_url:
        keys.append(f"url:{_digest(normalized_url)}")
    if guid:
        keys.append(f"guid:{publisher_id}:{_digest(str(guid).strip())}")
    normalized = normalize_title(title)
    if normalized:
        bucket = (published_at or "unknown")[:10]
        keys.append(f"title:{publisher_id}:{_digest(normalized + '|' + bucket)}")
    return keys


def article_id(primary_key: str) -> str:
    return f"art_{_digest(primary_key)[:16]}"
