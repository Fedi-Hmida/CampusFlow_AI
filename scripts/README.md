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
| | `regenerate_fictif.py` | `data/regs/fictitious/*_FICTIF.pdf` (label on every page, byte-reproducible) |
| | `build_consistency_review.py` | `eval/review/sheets/consistency_review.md` |
| | `manual_tables.json`, `fictif_corrections.json` | inputs: hand-serialised tables (A6), CF-108b corrections |
| `tables/` | `transform_calendar.py` | `data/tables/exam_calendar.csv`, `module_codes.csv` |
| | `fix_directory.py` | `data/tables/directory.csv` |
| | `fix_requests.py` | `data/tables/request_catalogue.csv`, `eval/review/sheets/request_mapping_review.md` |
| | `build_org_chart.py` | `diagrams/org_chart.mmd` |
| `testsets/` | `build_t1.py` | `eval/testsets/T1_regulations.csv`, `eval/review/sheets/T1_review.md` |
| | `build_tests_t2_t5.py` | `eval/testsets/T2…T5*.csv`, review sheets for T2/T3/T5 and the T4 prompts |
| | `degrade_t4.py` | blurry / rotated T4 photos from the sharp sources |
| (root) | `validate_data.py` | console report: schemas, cross-file links, labelling, privacy (exit 1 on error) |
| (root) | `run_all.py` | runs all of the above in order |

Review sheets are never overwritten once ticked (`[x]`): the builder writes `<name>_new.md` instead.
