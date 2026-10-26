# Router v1 — zero-shot vs few-shot (CF-022)

**Setup (26 Oct 2026):** template [P-ROUTER-001 v1](../../prompts/P-ROUTER-001.md), schema
[router.schema.json](../../prompts/schemas/router.schema.json) passed to Ollama as structured output, `qwen3:4b-instruct`
(CPU), temperature 0. Dev set: the 57 `router_dev = yes` rows of [D5 triage](../candidates/D5_triage.csv) (synthetic,
never T1–T5; labels by Doua, **not verified**). Few-shot = the 30 [Router examples](../../prompts/examples/router_examples.md)
as user / assistant turns. Script and raw outputs: [router_eval.py](router_eval.py), `router_results/`.

## Results
| Metric | Zero-shot | Few-shot (30 examples) |
|---|---:|---:|
| Valid JSON / schema-valid | 56 / 56 | **57 / 57** |
| Intents exactly right | 42 / 57 (74 %) | **46 / 57 (81 %)** |
| Intent overlap (mean Jaccard) | 0.77 | **0.83** |
| Language right | 56 / 57 | **57 / 57** |
| Regime **invented** (not stated by the student) | 7 | **0** |
| Regime missed (stated, left null) | 2 | 2 |
| Out-of-scope precision / recall | 0.33 / 0.25 | **1.00 / 0.60** |
| Seconds per call (CPU) | **25.0** | 52.8 |

## What the examples fixed
- **Invented regime:** zero-shot filled `regime = jour` on 7 calendar questions (D5-024…030, e.g. « Je suis en 1A12 »),
  i.e. inferred the regime from the class — exactly what the shared rules forbid. Few-shot: 0.
- **Out of scope:** zero-shot sent refusals (grades, absences count) to regulations / admin; few-shot never labels a
  real question out of scope (precision 1.00).

## The 11 few-shot misses
| Kind | Rows | Reading |
|---|---|---|
| Clear error | D5-047 « Quelle est ma note en Probabilités ? » → regulations | a personal-data request must be refused (out of scope) |
| Calendar vs regulations | D5-008 / 009 / 010 (retake registration delay, convocations, results) | dates of the session → calendar is defensible; the label says regulations |
| Extra intent | D5-020 / 021 / 041 → + admin | « who do I write to » is in the question → admin is defensible |
| Admin vs regulations | D5-055 / 056 / 061 (fees, payment, scholarships) → admin | the finance / mobility office owns these → defensible |
| Admin vs out of scope | D5-049 « Envoie un email … de ma part » → admin | Admin drafts without sending → defensible |

→ D5 labels need Fedi's review before they can score the Router; on the defensible readings few-shot is ≈ 56 / 57.

## Consequences
- Keep **few-shot** (no invented regime, no false refusal) but its cost is too high for the 90 s budget: **52.8 s** for the
  Router alone. Next (ADR-010): keep ≈ 10 examples covering the observed errors (regime from class, personal data,
  sending on behalf), and shrink the output (entities only when present) — output tokens dominate on CPU (4.1 tok/s).
- Add an explicit rule: « une demande sur ses propres notes ou absences est hors périmètre » (D5-047).
- Limits: one run, synthetic unverified labels, 57 rows.
