"""Text utilities for LinkAid UI (no Streamlit dependency)."""

from __future__ import annotations

import re

_PERSIAN_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")


def contains_rtl_text(text: str) -> bool:
    return bool(_PERSIAN_ARABIC.search(text))


def should_use_rtl(text: str, language_mix: str = "fa-en") -> bool:
    """Apply RTL when Persian/Arabic script is present (works for fa-en mixed content)."""
    _ = language_mix
    return contains_rtl_text(text)
