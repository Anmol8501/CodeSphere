import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str, max_length: int = 160) -> str:
    """"Two Sum!" -> "two-sum". Returns "" if nothing usable remains."""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = _NON_ALNUM.sub("-", ascii_value.lower()).strip("-")
    return slug[:max_length].rstrip("-")


def escape_like(term: str) -> str:
    """Escape LIKE wildcards so user input matches literally (use escape='\\')."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
