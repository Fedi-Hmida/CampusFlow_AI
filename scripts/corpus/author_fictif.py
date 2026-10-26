"""CF-117 — render the FICTITIOUS documents written by the project (no raw delivery) as labelled PDFs.

  in : scripts/corpus/authored_fictif.json   (D1-012 finance guide, D1-013 mobility guide)
  out: data/regs/fictitious/<target>.pdf      (same layout, label and footer as regenerate_fictif.py; byte-reproducible)
Checks, as for the regenerated procedures: label on every page, no "(cid:", every unit found again after extraction
with word similarity >= 0.98. extract_regs.py then reads these PDFs like the other FICTITIOUS documents.
Run: .venv/Scripts/python scripts/corpus/author_fictif.py   (then scripts/corpus/extract_regs.py)
"""
import difflib
import json
import sys
from pathlib import Path

import pdfplumber

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "lib"), str(Path(__file__).resolve().parent)]
import extract_regs as ex  # noqa: E402
import regenerate_fictif as rf  # noqa: E402

SRC = Path(__file__).resolve().parent / "authored_fictif.json"


def main() -> None:
    ok = True
    titles = {d[0]: d[3] for d in ex.DOCS}
    for d in json.loads(SRC.read_text(encoding="utf-8"))["docs"]:
        units = d["units"]
        assert titles.get(d["doc_id"]) == d["title"], f"{d['doc_id']}: title differs from extract_regs.DOCS"
        out = ex.OUT / "fictitious" / d["target"]
        out.parent.mkdir(parents=True, exist_ok=True)
        rf.render(out, d["title"], d["ref"], units)
        with pdfplumber.open(str(out)) as pdf:
            toc = {}
            pages = [[ln for ln in ex.page_lines(d["doc_id"], p, {}, toc) if ln != rf.LABEL] for p in pdf.pages]
            label_pages = sum(rf.LABEL in (p.extract_text() or "") for p in pdf.pages)
        got = {u["number"]: u for u in ex.split_units(d["doc_id"], pages, toc)}
        sims = [difflib.SequenceMatcher(None, rf.words(u["text"]), rf.words(got[n]["text"]) if (n := u.get("number", "0")) in got else []).ratio()
                for u in units]
        cid = sum("(cid:" in "\n".join(p) for p in pages)
        worst = min(sims)
        ok &= worst >= 0.98 and cid == 0 and label_pages == len(pages) and len(got) == len(units)
        print(f"{d['doc_id']} → {d['target']}: pages {len(pages)}, label on {label_pages}/{len(pages)}, "
              f"units {len(got)}/{len(units)}, min similarity {worst:.3f}, (cid: {cid}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
