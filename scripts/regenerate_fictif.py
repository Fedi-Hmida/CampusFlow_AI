"""CF-104 — regenerate and label the 8 FICTITIOUS procedures (ADR-013, A1, A2).

Reads the untouched synthetic PDFs from data/raw/regs/, applies the CF-108b corrections (scripts/fictif_corrections.json),
and writes data/regs/*_FICTIF.pdf with:
  - "DOCUMENT FICTIF — projet CampusFlow AI, non officiel" in the header of every page;
  - the reference footer drawn in the bottom margin (outside the text flow);
  - metadata title "[FICTIF] <title>"; Arial TTF so bullets render as "•".
Checks: word-level similarity of each article with its (corrected) source ≥ 0.98 and 0 "(cid:" after re-extraction.
Run: .venv/Scripts/python scripts/regenerate_fictif.py   (then re-run scripts/extract_regs.py)
"""
import difflib
import json
import re
import sys
from pathlib import Path

import pdfplumber
from reportlab import rl_config

rl_config.invariant = 1  # fixed creation date and document ID → two builds are byte-identical (reproducibility)
from reportlab.lib.enums import TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
import extract_regs as ex  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LABEL = "DOCUMENT FICTIF — projet CampusFlow AI, non officiel"
pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
BODY = ParagraphStyle("body", fontName="Arial", fontSize=10, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=3)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=14, bulletIndent=4)
HEAD = ParagraphStyle("head", fontName="Arial-Bold", fontSize=11, leading=14, spaceBefore=8, spaceAfter=4)
TITLE = ParagraphStyle("title", fontName="Arial-Bold", fontSize=14, leading=18, spaceAfter=6)


def words(s: str) -> list[str]:
    s = " ".join(l for l in s.splitlines() if not l.startswith("[Tableau"))  # layout marker, not content
    return re.findall(r"\w+", s.lower())


def paragraphs(text: str) -> list[str]:
    """Re-join wrapped PDF lines into paragraphs; bullets start a new paragraph."""
    out = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if not out or ln.startswith("•") or re.match(r"^(Cours du|Alternance|Délai|Le dossier|La |Si |En cas)", ln) and out[-1].endswith((".", ":", ";")):
            out.append(ln)
        else:
            out[-1] += " " + ln
    return out


def apply_corrections(doc_id: str, units: list[dict], corr: list[dict]) -> list[str]:
    done = []
    for c in (c for c in corr if c["doc_id"] == doc_id):
        pat = re.compile(r"\s+".join(map(re.escape, c["old"].split())))
        for u in units:
            if u["number"] == c["article"] and pat.search(u["text"]):
                u["text"] = pat.sub(c["new"].replace("\\", "\\\\"), u["text"], count=1)
                done.append(c["id"])
    return done


def render(path: Path, title: str, ref: str, units: list[dict]) -> None:
    def deco(canvas, docx):
        canvas.saveState()
        canvas.setFont("Arial-Bold", 9); canvas.setFillColorRGB(0.75, 0.1, 0.1)
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, LABEL)
        canvas.setFont("Arial", 8); canvas.setFillColorRGB(0.3, 0.3, 0.3)
        canvas.drawString(2 * cm, 1.0 * cm, f"{ref} | FICTIF | Page {docx.page}")
        canvas.restoreState()

    story = []
    for u in units:
        lines = u["text"].splitlines()
        if u["level"] == "preamble":  # school name, title, version, then "Clé : valeur" lines of the header table
            for i, p in enumerate(l for l in lines if l.strip() and not l.startswith("[Tableau")):
                story.append(Paragraph(escape(p), TITLE if i == 1 else BODY))
            story.append(Spacer(1, 6))
            continue
        story.append(Paragraph(escape(lines[0]), HEAD))
        for p in paragraphs("\n".join(lines[1:])):
            if p.startswith("•"):
                story.append(Paragraph(escape(p.lstrip("• ").strip()), BULLET, bulletText="•"))
            else:
                story.append(Paragraph(escape(p), BODY))
        story.append(Spacer(1, 2))
    d = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
                          title=f"[FICTIF] {title}", author="CampusFlow AI (document fictif)", subject=LABEL)
    d.build(story, onFirstPage=deco, onLaterPages=deco)


def main() -> None:
    corr = json.loads((ROOT / "scripts/fictif_corrections.json").read_text(encoding="utf-8"))
    applied, ok = [], True
    for doc_id, raw, target, title, regime, status, *_ in ex.DOCS:
        if status != "FICTITIOUS":
            continue
        with pdfplumber.open(str(ex.RAW / raw)) as pdf:
            toc = {}
            pages = [ex.page_lines(doc_id, p, {}, toc) for p in pdf.pages]
        units = ex.split_units(doc_id, pages, toc)
        ref = next((re.search(r"ESPRIT-[A-Z]+-\d+", u["text"]).group(0) for u in units if re.search(r"ESPRIT-[A-Z]+-\d+", u["text"])), "ESPRIT-FICTIF")
        applied += apply_corrections(doc_id, units, corr)
        out = ex.OUT / target
        render(out, title, ref, units)
        # verification: re-extract and compare article by article
        with pdfplumber.open(str(out)) as pdf:
            toc2 = {}
            pages2 = [[l for l in ex.page_lines(doc_id, p, {}, toc2) if l != LABEL] for p in pdf.pages]
            label_pages = sum(LABEL in (p.extract_text() or "") for p in pdf.pages)
            n_pages = len(pdf.pages)
        units2 = {u["number"]: u for u in ex.split_units(doc_id, pages2, toc2)}
        sims = []
        for u in units:
            v = units2.get(u["number"])
            sims.append(difflib.SequenceMatcher(None, words(u["text"]), words(v["text"]) if v else []).ratio())
        cid = sum("(cid:" in "\n".join(p) for p in pages2)
        worst = min(sims)
        ok &= worst >= 0.98 and cid == 0 and label_pages == n_pages and len(units2) == len(units)
        print(f"{doc_id} → {target}: pages {n_pages}, label on {label_pages}/{n_pages}, units {len(units2)}/{len(units)}, "
              f"min similarity {worst:.3f}, (cid: {cid}")
    print(f"corrections applied: {sorted(applied)} (expected {sorted(c['id'] for c in corr)})")
    sys.exit(0 if ok and sorted(applied) == sorted(c["id"] for c in corr) else 1)


if __name__ == "__main__":
    main()
