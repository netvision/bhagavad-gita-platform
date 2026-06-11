import html
import re
from pathlib import PurePath


_BLOCK_TAG_RE = re.compile(r"</?(p|div|br|li|ol|ul|h[1-6]|tr|section|article)\b[^>]*>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SPACE_RE = re.compile(r"[ \t]+")
_BLANK_LINE_RE = re.compile(r"\n{3,}")


def sanitize_text(value: object) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value))
    text = _SCRIPT_RE.sub("", text)
    text = _BLOCK_TAG_RE.sub("\n", text)
    text = _TAG_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(_SPACE_RE.sub(" ", line).strip() for line in text.split("\n"))
    text = _BLANK_LINE_RE.sub("\n\n", text).strip()
    return text or None


def sanitize_required_text(value: object) -> str:
    text = sanitize_text(value)
    if not text:
        raise ValueError("Value is required")
    return text


def sanitize_file_key(value: object) -> str | None:
    text = sanitize_text(value)
    if not text:
        return None
    name = PurePath(text).name
    if name in {"", ".", ".."}:
        return None
    return name
