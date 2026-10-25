"""Helpers to locate exact quotes and article keys in the cleaned corpus (data/regs/clean/).

Used by the review-sheet builders and by scripts/validate_data.py. Matching ignores whitespace, line breaks and
typographic apostrophes, so a quote copied from the PDF matches the extracted text.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

CLEAN = Path(__file__).resolve().parents[1] / "data/regs/clean"


def canon(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("«", '"').replace("»", '"').replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


@lru_cache(maxsize=None)
def doc(doc_id: str) -> dict:
    return json.loads((CLEAN / f"{doc_id}.json").read_text(encoding="utf-8"))


def all_doc_ids() -> list[str]:
    return sorted(p.stem for p in CLEAN.glob("D1-*.json"))


def article_keys(doc_id: str | None = None) -> set[str]:
    ids = [doc_id] if doc_id else all_doc_ids()
    return {u["key"] for i in ids for u in doc(i)["articles"]}


def find_quote(doc_id: str, quote: str) -> dict | None:
    """Return {page, key} of the first page / article unit containing the quote, or None."""
    q = canon(quote)
    d = doc(doc_id)
    page = next((p["page"] for p in d["pages"] if q in canon(p["text"])), None)
    if page is None:  # quote may straddle a page break
        joined = canon(" ".join(p["text"] for p in d["pages"]))
        if q not in joined:
            return None
    key = next((u["key"] for u in d["articles"] if q in canon(u["text"])), None)
    if page is None and key:
        page = next(u["page_start"] for u in d["articles"] if u["key"] == key)
    return {"page": page, "key": key}


def longest_shared_run(a: str, b: str) -> int:
    """Length (in words) of the longest run of consecutive words of `a` that also appears in `b`."""
    wa = re.findall(r"\w+", canon(a))
    tb = " " + " ".join(re.findall(r"\w+", canon(b))) + " "
    best = 0
    for i in range(len(wa)):
        for j in range(i + best + 1, len(wa) + 1):
            if " " + " ".join(wa[i:j]) + " " in tb:
                best = j - i
            else:
                break
    return best
