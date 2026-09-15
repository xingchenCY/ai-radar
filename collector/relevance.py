from __future__ import annotations

import re
import unicodedata


POSITIVE_2 = [
    "人工智能", "大模型", "生成式 ai", "机器学习", "深度学习", "llm", "large language model",
    "gpt", "claude", "gemini", "deepseek", "openai", "anthropic", "mistral",
]
POSITIVE_1 = ["agent", "agentic", "智能体", "模型", "推理", "训练", "ai"]
NEGATIVE_2 = ["ai 手机", "ai手机", "ai 摄影", "ai摄影", "ai 修图", "ai修图"]


def relevance_score(title: str, summary: str, mode: str) -> tuple[int, list[str], str]:
    if mode == "ai_feed":
        return 3, [], "ai_feed"
    haystack = unicodedata.normalize("NFKC", f"{title} {summary}").casefold()
    score = 0
    matched: list[str] = []
    for term in POSITIVE_2:
        if term.casefold() in haystack:
            score += 2
            matched.append(term)
    for term in POSITIVE_1:
        if term.casefold() in haystack and term not in matched:
            score += 1
            matched.append(term)
    for term in NEGATIVE_2:
        if term.casefold() in haystack:
            score -= 2
    if not re.search(r"[a-zA-Z\u4e00-\u9fff]", title):
        score -= 2
    status = "high" if score >= 2 else "possible" if score == 1 else "rejected"
    return score, matched[:8], status

