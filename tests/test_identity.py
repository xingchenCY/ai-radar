from collector.identity import canonical_url, identity_keys, normalize_title


def test_tracking_parameters_and_fragment_are_removed() -> None:
    assert canonical_url("HTTPS://Example.com:443/story/?utm_source=x&ref=home&id=7#comments") == "https://example.com/story?id=7"


def test_identity_falls_back_from_url_to_guid_to_title() -> None:
    with_url = identity_keys(publisher_id="p", url="https://example.com/a", guid="g", title="Title", published_at="2026-09-14T00:00:00Z")
    assert with_url[0].startswith("url:")
    assert any(key.startswith("guid:p:") for key in with_url)
    assert any(key.startswith("title:p:") for key in with_url)
    no_url = identity_keys(publisher_id="p", url="", guid="g", title="Title", published_at=None)
    assert no_url[0].startswith("guid:p:")
    no_url_or_guid = identity_keys(publisher_id="p", url="", guid=None, title="AI!  News", published_at=None)
    assert no_url_or_guid[0].startswith("title:p:")
    assert normalize_title(" AI!  News ") == "ai news"
