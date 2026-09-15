from collector.plain_text import to_plain_text


def test_html_is_converted_to_text_and_script_is_not_executed() -> None:
    value = to_plain_text('<p>Hello <strong>AI</strong></p><script>alert(1)</script><p>Radar<br>today</p>')
    assert value == "Hello AI\nRadar\ntoday"
    assert "alert" not in value


def test_plain_text_is_bounded() -> None:
    value = to_plain_text("x" * 500, max_length=10)
    assert value == "xxxxxxxxxx…"


def test_malformed_markup_returns_safe_text() -> None:
    value = to_plain_text('<div>unfinished <b>markup')
    assert "unfinished" in value


def test_promotional_footer_is_removed() -> None:
    value = to_plain_text("<p>真正的文章摘要</p><p>#欢迎关注爱范儿官方微信公众号：爱范儿（微信号：ifanr），更多精彩内容第一时间为您奉上。</p>")
    assert value == "真正的文章摘要"


def test_inline_promotional_tail_is_removed_without_losing_summary() -> None:
    value = to_plain_text("正文摘要 #欢迎关注爱范儿官方微信公众号：爱范儿（微信号：ifanr），更多精彩内容第一时间为您奉上。")
    assert value == "正文摘要"
