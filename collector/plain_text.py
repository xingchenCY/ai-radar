from __future__ import annotations

import re
from html.parser import HTMLParser


_PROMOTIONAL_TAIL_PATTERNS = (
    r"(?:#\s*)?欢迎关注[^\n]*",
    r"点击关注[^\n]*公众号[^\n]*",
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript", "template"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth == 0 and normalized in {"br", "p", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript", "template"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if self._ignored_depth == 0 and normalized in {"p", "div", "li"}:
            self.parts.append("\n")


def to_plain_text(value: str | None, max_length: int = 420) -> str:
    if not value:
        return ""
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
        text = "".join(parser.parts)
    except Exception:
        return ""
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    for pattern in _PROMOTIONAL_TAIL_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    return text[:max_length].rstrip() + ("…" if len(text) > max_length else "")
