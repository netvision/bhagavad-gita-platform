from html import escape
from html.parser import HTMLParser

import bleach


ALLOWED_HTML_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "s",
    "h2",
    "h3",
    "h4",
    "ul",
    "ol",
    "li",
    "blockquote",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "a",
]

ALLOWED_HTML_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}


class _LinkRelNormalizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            attrs = self._normalize_link_attrs(attrs)
        self.parts.append(f"<{tag}{self._format_attrs(attrs)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(f"<{tag}{self._format_attrs(attrs)}>")

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self.parts)

    def _normalize_link_attrs(
        self, attrs: list[tuple[str, str | None]]
    ) -> list[tuple[str, str | None]]:
        rel_index = next((i for i, (name, _) in enumerate(attrs) if name == "rel"), None)
        rel_tokens: list[str] = []
        if rel_index is not None and attrs[rel_index][1]:
            rel_tokens = attrs[rel_index][1].split()

        for token in ("noreferrer", "noopener"):
            if token not in rel_tokens:
                rel_tokens.append(token)

        normalized_rel = " ".join(rel_tokens)
        if rel_index is None:
            return [*attrs, ("rel", normalized_rel)]

        normalized_attrs = list(attrs)
        normalized_attrs[rel_index] = ("rel", normalized_rel)
        return normalized_attrs

    def _format_attrs(self, attrs: list[tuple[str, str | None]]) -> str:
        if not attrs:
            return ""
        return "".join(
            f' {name}="{escape(value, quote=True)}"' if value is not None else f" {name}"
            for name, value in attrs
        )


def sanitize_html(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = bleach.clean(
        value,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
        strip_comments=True,
    )
    normalizer = _LinkRelNormalizer()
    normalizer.feed(cleaned)
    normalizer.close()
    return normalizer.get_html()


sanitize_rich_html = sanitize_html
