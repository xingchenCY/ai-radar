from collector.relevance import relevance_score


def test_ai_feed_is_kept_without_keyword_guessing() -> None:
    score, terms, status = relevance_score("Quarterly note", "No keyword", "ai_feed")
    assert (score, terms, status) == (3, [], "ai_feed")


def test_broad_feed_scores_positive_and_marketing_noise_negative() -> None:
    score, terms, status = relevance_score("大模型训练平台", "支持 LLM 推理", "broad")
    assert score >= 2 and terms and status == "high"
    score, _, status = relevance_score("AI 手机摄影体验", "AI 修图功能", "broad")
    assert score <= 0 and status == "rejected"
