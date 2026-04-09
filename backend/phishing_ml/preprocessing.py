"""Text cleaning before vectorization."""

import re

# Remove most punctuation/symbols; keep word tokens and spaces for TF-IDF + English stopwords.
_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """
    Normalize email text: lowercase, strip punctuation, collapse whitespace.
    Stopwords are removed by TfidfVectorizer(stop_words='english').
    """
    if not isinstance(text, str):
        return ""
    s = text.lower()
    s = _NON_WORD.sub(" ", s)
    s = _WHITESPACE.sub(" ", s).strip()
    return s
