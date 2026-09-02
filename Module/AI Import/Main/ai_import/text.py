from __future__ import annotations

import re
import unicodedata


_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[^0-9a-zA-ZÀ-ỹ#]+", re.UNICODE)


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    text = _PUNCT.sub(" ", text)
    return _SPACE.sub(" ", text).strip()


def fold_vietnamese(value: object) -> str:
    text = normalize_text(value).replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def tokens(value: object) -> set[str]:
    return {part for part in fold_vietnamese(value).split(" ") if len(part) > 1}

