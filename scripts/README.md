# scripts/

Everything under `data/regs/`, `data/tables/` and `eval/` is generated from the untouched delivery in `data/raw/`.
Rebuild all of it, then validate, with one command (inside the repo's `.venv`):

```powershell
.venv\Scripts\python scripts\run_all.py
```

| Folder | Script | Output |
|---|---|---|
| `lib/` | `corpus_lookup.py` | shared helpers: quote lookup, article keys, review-sheet writer |
| `corpus/` | `extract_regs.py` | `data/regs/clean/D1-*.json`, `data/regs/official/*.pdf` (author metadata removed) |
| | `author_fictif.py` | `data/regs/fictitious/` D1-012 / D1-013 from `authored_fictif.json` (CF-117) |
| | `regenerate_fictif.py` | `data/regs/fictitious/*_FICTIF.pdf` (label on every page, byte-reproducible) |
| | `build_consistency_review.py` | `eval/review/sheets/consistency_review.md` |
| | `manual_tables.json`, `fictif_corrections.json` | inputs: hand-serialised tables (A6), CF-108b corrections |
| `index/` | `build_chunks.py` | `data/index/chunks_A.json`, `chunks_B.json`, `README.md` (CF-016) |
| `tables/` | `transform_calendar.py` | `data/tables/exam_calendar.csv`, `module_codes.csv` |
| | `fix_directory.py` | `data/tables/directory.csv` |
| | `fix_requests.py` | `data/tables/request_catalogue.csv`, `eval/review/sheets/request_mapping_review.md` |
| | `build_org_chart.py` | `diagrams/org_chart.mmd` |
| `testsets/` | `build_t1.py` | `eval/testsets/T1_regulations.csv`, `eval/review/sheets/T1_review.md` |
| | `build_tests_t2_t5.py` | `eval/testsets/T2_calendar.csv`, `T3_contacts_requests.csv`, `T5_adversarial.csv`, `eval/review/sheets/T2_T3_T5_review.md` |
| | `build_t4.py` | `eval/testsets/T4_photos.csv` (ground truth of the photos, Vision schema keys), `eval/review/sheets/T4_review.md` |
| | `degrade_t4.py` | `T4-09` blurry, `T4-10` rotated (from Ines's sharp photos), `T4-11` drawn unrelated image |
| | `triage_d5.py` | `eval/candidates/D5_triage.csv` — status per D5 candidate row + Router dev labels (not a test set) |
| (root) | `validate_data.py` | console report: schemas, cross-file links, labelling, prompt library, Markdown links, privacy (exit 1 on error) |
| (root) | `run_all.py` | runs all of the above in order |

Review sheets are never overwritten once ticked (`[x]`): the builder writes `<name>_new.md` instead.
