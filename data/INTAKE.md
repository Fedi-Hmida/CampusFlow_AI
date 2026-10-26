# Data intake — how a new delivery enters the project

Any document or table that a test, a prompt example or an answer cites must enter through this procedure first. Files
used only on someone's laptop (e.g. the « second dataset » behind `eval/candidates/D5_original_2026-10-25.csv`)
**cannot be cited** until they are imported.

## Second dataset (Doua, 25 Oct 2026) — not delivered, replaced (CF-117, 26 Oct)
The files were never available. Two FICTITIOUS guides written by the project cover the same needs without inventing
official facts: D1-012 (paying fees, payment plans — no amounts) and D1-013 (exchange, double degree — no internships
abroad). If the original files arrive later, they still follow the procedure below with new doc_ids (D1-014+).
| Content seen in D5 / Router examples | Status |
|---|---|
| New validation / retake regulation and absences regulation (named `D1-002`, `D1-003` in that delivery) | **not imported** — those IDs belong to the evening and work-study regulations here |
| Finance guide (tuition fees, payment, discounts), mobility guide (exchange, double degrees, Erasmus+) | not imported |
| Exam calendar 2026-2027 with rooms and end times, academic periods, `D2_modules.csv`, `D2_classes.csv` | not imported |

## Project-authored FICTITIOUS documents
Source text in `scripts/corpus/authored_fictif.json` (never in `data/raw/`, which holds deliveries only), rendered by
`scripts/corpus/author_fictif.py` with the same label, footer and checks as the regenerated procedures, then registered
in `DOCS` of `extract_regs.py` with `raw = AUTHORED`.

## Procedure for a delivery (Fedi runs it; the owner of the files sends them)
1. **Deliver**: the owner shares the original files (no edits, no renaming).
2. **Copy byte-for-byte** into `data/raw/regs/` or `data/raw/tables/` (`cp -p`), never edit them afterwards.
3. **Checksum**: add one row per file to [raw/MANIFEST.md](raw/MANIFEST.md) (source, target, size, SHA-256, kept/excluded, reason).
4. **Decide** each file: kept / excluded (duplicate, outdated, personal data) — write the reason in the manifest and an ADR
   in the decisions log.
5. **New IDs only**: regulations get the next free doc_id (`D1-014`, …). **Never reuse D1-001…D1-013.**
   Set `regime` (jour | soir | alternance | all | `;`-list) and `doc_status` (official | FICTITIOUS).
6. **Extract**: add the doc to `DOCS` in `scripts/corpus/extract_regs.py`; tables get their own transform script in
   `scripts/tables/`. A new calendar with rooms replaces projected rows only through an explicit ADR.
7. **Rebuild + validate**: `.venv/Scripts/python scripts/run_all.py` → 0 errors; update `data/regs/CORPUS_CARD.md`.
8. **Re-triage** `eval/candidates/` (`triage_d5.py` runs inside `run_all`); rows that become `supported` can then be
   rewritten as test candidates and ticked.
