# eval/candidates/ — NOT test sets

Files here are **candidates**: useful material whose answers are not (yet) backed by the approved data. Never cite them as
evaluation results, and never copy their questions into prompts.

| File | What it is | Use |
|---|---|---|
| `D5_original_2026-10-25.csv` | Doua's synthetic question set (CF-205), kept verbatim (61 rows, UTF-8 with BOM). | Source only. |
| `D5_triage.csv` | Built by `scripts/testsets/triage_d5.py`: a new `D5-NNN` id per row, the regime named in the question, the Router intents, a status and the reasons. | `router_dev = yes` rows → **Router development set** (intent + language + missing regime). |

## Status meaning (current counts in the script output)
| Status | Meaning | Count |
|---|---|---|
| `blocked_source` | The expected answer cites a source that is absent from `data/regs/clean` / `data/tables`, or the cited article says something else. Most rows come from the second dataset (new D1-002/D1-003 PDFs, finance and mobility guides, calendar with rooms) that was never imported — see [data/INTAKE.md](../../data/INTAKE.md). | 44 |
| `rule_conflict` | The answer contradicts approved data (regime-blind medical-certificate rule vs D1-001/7-8 for *cours du jour*; old 3-day REQ-08 delay). | 4 |
| `leak` | ≥ 6 consecutive words shared with an official T1–T5 question → excluded from every dev use. | 3 |
| `route_only` | Refusal / injection / out-of-scope: no source fact to check; routing label is valid. | 7 |
| `supported` | Every number and ≥ 60 % of the content words appear in the cited approved sources (checked by hand too). | 3 |

## How a row becomes a test row
1. Its source is in the approved data (import via `data/INTAKE.md` if needed, with a **new** doc_id).
2. The answer is rewritten from that source, with the regime when the rule depends on it.
3. Fedi ticks it (`verified_by`) and it moves to the right `eval/testsets/T*.csv` with that set's id scheme.
