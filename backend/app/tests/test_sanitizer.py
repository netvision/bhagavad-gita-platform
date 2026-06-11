from app.core.sanitizer import sanitize_rich_html


def test_script_tags_are_removed() -> None:
    sanitized = sanitize_rich_html('<p>Hello</p><script>alert("xss")</script>')

    assert sanitized == "<p>Hello</p>alert(\"xss\")"
    assert "<script" not in sanitized


def test_allowed_rich_content_is_preserved() -> None:
    html = "<h2>Heading</h2><blockquote>Quote</blockquote><ul><li>Item</li></ul>"

    assert sanitize_rich_html(html) == html


def test_links_disallow_javascript_urls_and_add_rel() -> None:
    sanitized = sanitize_rich_html(
        '<p><a href="javascript:alert(1)" target="_blank">Bad</a> '
        '<a href="https://example.com" target="_blank">Good</a></p>'
    )

    assert 'href="javascript:' not in sanitized
    assert '<a target="_blank" rel="noreferrer noopener">Bad</a>' in sanitized
    assert (
        '<a href="https://example.com" target="_blank" rel="noreferrer noopener">'
        "Good</a>"
    ) in sanitized
