"""CF-016 — build the chunks of strategy A (fixed windows) and B (article / sub-section units) from data/regs/clean.

  A  fixed windows of 2 000 characters (≈ 500 tokens at 4 chars/token, corpus-card convention) with 200 of overlap, cut
     at whitespace, over the article-ordered text of each document; no structure-aware header. Each chunk still lists
     the article keys it overlaps by >= 100 characters (biggest overlap first), so T1 can be scored on A as well.
  B  one chunk per article / sub-section; heading-only units (< 100 characters, e.g. "Article 7 : Régime des examens")
     are merged into the next unit (both keys kept); units > 2 000 characters are split at line boundaries and every
     part repeats the article heading. Each chunk text starts with the document title (contextual header).
Every FICTITIOUS chunk starts with the label (A2). point_id = uuid5(chunk_id): re-indexing never duplicates points.
Outputs: data/index/chunks_A.json, data/index/chunks_B.json, data/index/README.md
Run: .venv/Scripts/python scripts/index/build_chunks.py
"""
import json
import statistics
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from corpus_lookup import all_doc_ids, doc  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/index"
LABEL = "[DOCUMENT FICTIF — projet CampusFlow AI, non officiel]"
SIZE, OVERLAP, MIN_UNIT, MIN_KEY_OVERLAP = 2000, 200, 100, 100
NS = uuid.UUID("6f6b2a4e-7c3a-4d1e-9a51-0c4e5f3a2b10")  # fixed namespace for point ids


def body_of(unit: dict) -> str:
    t = unit["text"]
    return t[len(LABEL):].lstrip("\n") if t.startswith(LABEL) else t


def regimes(regime: str) -> list[str]:
    return ["jour", "soir", "alternance"] if regime == "all" else regime.split(";")


def record(strategy: str, n: int, d: dict, keys: list[str], units: list[dict], body: str, header: str = "") -> dict:
    cid = f"{strategy}:{d['doc_id']}:{n:03d}"
    label = LABEL + "\n" if d["doc_status"] == "FICTITIOUS" else ""
    return {"chunk_id": cid, "point_id": str(uuid.uuid5(NS, cid)), "strategy": strategy, "doc_id": d["doc_id"],
            "doc_title": d["title"], "doc_status": d["doc_status"], "regime": d["regime"], "regimes": regimes(d["regime"]),
            "article_keys": keys, "page_start": min(u["page_start"] for u in units), "page_end": max(u["page_end"] for u in units),
            "body": body, "text": label + (header + "\n" if header else "") + body, "chars": len(body)}


def cut(text: str, start: int, end: int) -> int:
    """Move `end` back to the last whitespace (keeps words whole), never below start + 3/4 of the window."""
    if end >= len(text):
        return len(text)
    ws = text.rfind(" ", start + SIZE * 3 // 4, end)
    nl = text.rfind("\n", start + SIZE * 3 // 4, end)
    return max(ws, nl) if max(ws, nl) > 0 else end


def strategy_a(d: dict) -> list[dict]:
    parts, spans, pos = [], [], 0
    for u in d["articles"]:
        b = body_of(u)
        parts.append(b)
        spans.append((pos, pos + len(b), u))
        pos += len(b) + 1
    text = "\n".join(parts)
    out, start, n = [], 0, 0
    while start < len(text):
        end = cut(text, start, start + SIZE)
        overlaps = [(min(end, e) - max(start, s), u) for s, e, u in spans if min(end, e) - max(start, s) > 0]
        keep = [(ov, u) for ov, u in overlaps if ov >= MIN_KEY_OVERLAP or ov == len(body_of(u))] or [max(overlaps, key=lambda x: x[0])]
        keep.sort(key=lambda x: -x[0])
        n += 1
        out.append(record("A", n, d, [u["key"] for _, u in keep], [u for _, u in keep], text[start:end].strip()))
        if end >= len(text):
            break
        nxt = end - OVERLAP
        sp = text.find(" ", nxt, end)
        start = sp + 1 if sp != -1 else nxt
    return out


def split_lines(body: str) -> list[str]:
    """Split a long unit into parts of <= SIZE characters. PDF lines wrap inside sentences, so a part ends on the last
    line that closes a sentence or a list item (. ; :) in the second half of the part; a plain line break otherwise."""
    parts, buf = [], []
    for ln in body.split("\n"):
        if sum(len(x) + 1 for x in buf) + len(ln) > SIZE and buf:
            ends = [k for k, x in enumerate(buf) if x.rstrip().endswith((".", ";", ":"))
                    and sum(len(y) + 1 for y in buf[:k + 1]) >= SIZE // 2]
            k = ends[-1] if ends else len(buf) - 1
            parts.append("\n".join(buf[:k + 1]).strip())
            buf = buf[k + 1:]
        buf.append(ln)
    if "\n".join(buf).strip():
        parts.append("\n".join(buf).strip())
    return parts


def strategy_b(d: dict) -> list[dict]:
    out, n, carry = [], 0, []
    units = d["articles"]
    for i, u in enumerate(units):
        if len(body_of(u)) < MIN_UNIT and i + 1 < len(units):
            carry.append(u)
            continue
        group = carry + [u]
        carry = []
        body = "\n".join(body_of(x) for x in group)
        heading = body.split("\n", 1)[0]
        for j, part in enumerate(split_lines(body)):
            n += 1
            header = d["title"] + ("" if j == 0 else f"\n{heading} (suite)")
            out.append(record("B", n, d, [x["key"] for x in group], group, part, header))
    return out


def describe(name: str, ch: list[dict]) -> list[str]:
    sizes = [c["chars"] for c in ch]
    per_doc = {}
    for c in ch:
        per_doc[c["doc_id"]] = per_doc.get(c["doc_id"], 0) + 1
    return [f"| {name} | {len(ch)} | {min(sizes)} | {int(statistics.mean(sizes))} | {max(sizes)} | "
            f"{statistics.mean(len(c['article_keys']) for c in ch):.2f} | {' · '.join(f'{k[3:]}: {v}' for k, v in per_doc.items())} |"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    docs = [doc(i) for i in all_doc_ids()]
    a = [c for d in docs for c in strategy_a(d)]
    b = [c for d in docs for c in strategy_b(d)]
    for name, ch in (("A", a), ("B", b)):
        (OUT / f"chunks_{name}.json").write_text(json.dumps(ch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    readme = ["# data/index — chunks for the two indexing strategies (CF-016)", "",
              "Generated by `scripts/index/build_chunks.py` from `data/regs/clean/` (do not edit). Indexed by WF-1",
              "(`workflows/01_wf1_index_regs.json`) into Qdrant: A → `regs_fixed`, B → `regs_structured`.", "",
              "| Strategy | Chunks | Min chars | Mean chars | Max chars | Article keys / chunk | Chunks per document |",
              "|---|---:|---:|---:|---:|---:|---|"] + describe("A — fixed 2 000 chars, overlap 200", a) + describe("B — article / sub-section", b) + [
              "", "Payload of every point: chunk_id, strategy, doc_id, doc_title, doc_status, regime, regimes[], article_keys[],",
              "page_start, page_end, text. Embedded text = `text` (label + header for B + body)."]
    (OUT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8", newline="\n")
    print(f"strategy A: {len(a)} chunks · strategy B: {len(b)} chunks → data/index/")


if __name__ == "__main__":
    main()
