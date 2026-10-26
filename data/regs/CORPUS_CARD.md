# Corpus card — CampusFlow AI regulations (D1)

| Field | Value |
|---|---|
| Purpose | Knowledge base for the Regulations agent (RAG): exams, retakes, absences, grading, internships, discipline, registration |
| Documents | **13** (3 official regulations + 8 FICTITIOUS procedures + 2 FICTITIOUS guides written by the project, CF-117) — ADR-012, ADR-024 |
| Pages / characters / est. tokens | 61 pages · 127 766 characters · ≈ 31 900 tokens (4 characters per token, French) |
| Structure | 115 articles + 27 sub-sections (`7-1 … 7-10`), keyed `<doc_id>/<number>/<title>` |
| Chunks | built by `scripts/index/build_chunks.py` (CF-016) |
| Format | PDF with selectable text (no OCR needed); cleaned text in `data/regs/clean/<doc_id>.json` |
| Language | French |
| Period | academic year 2024-2025 (official texts created Oct 2024 – May 2025) |
| Source | official: ESPRIT regulations delivered by the team (raw copies in `data/raw/regs/`, SHA-256 in `data/raw/MANIFEST.md`); FICTITIOUS: written by the team on 24 Oct 2026, corrected (CF-108b) and regenerated with a "DOCUMENT FICTIF" label (CF-104); D1-012/013 written by the project on 26 Oct 2026 (`scripts/corpus/authored_fictif.json`, CF-117) |
| Privacy | author metadata stripped from the official PDFs; no personal names, e-mails or phone numbers in the cleaned text (validator) |
| Built by | `scripts/corpus/extract_regs.py`, `scripts/corpus/regenerate_fictif.py` (25 Oct 2026), `scripts/corpus/author_fictif.py` (26 Oct 2026) |

## Documents

| doc_id | File (`data/regs/official/` · `data/regs/fictitious/`) | Title | Regime | doc_status | Pages | Characters | Articles + sub-sections | Date | Why it fits |
|---|---|---|---|---|---|---|---|---|---|
| D1-001 | reglement_scolarite-cours-du-jour_2024-2025.pdf | Règlement de scolarité 2024-2025 — Cours du jour | jour | official | 19 | 35 063 | 12 + 10 | 2025-05-11 | Core rules for day students: exams, retakes, absences (7-8), internships and PFE (7-9, 7-10), discipline |
| D1-002 | reglement_scolarite-cours-du-soir_2024-2025.pdf | Règlement de scolarité 2024-2025 — Cours du soir | soir | official | 13 | 29 519 | 14 + 9 | 2024-11-19 | Evening-course rules (48 h absence rule, double correction, sanctions list) |
| D1-003 | reglement_scolarite-alternance_2024-2025.pdf | Règlement & Engagement — Formation par alternance 2024-2025 | alternance | official | 12 | 30 327 | 13 + 8 | 2024-11-19 | Work-study rules (contract-linked exclusion, 45 ECTS, 48 h rule); two articles numbered 12 in the source |
| D1-004 | procedure_absences-justificatifs-rattrapage_2024-2025_FICTIF.pdf | Procédure : absences, justificatifs et sessions de rattrapage | all | FICTITIOUS | 2 | 6 102 | 8 | 2026-10-24 | Step-by-step absence / retake procedure per regime (forms, documents) |
| D1-005 | procedure_amenagements-examens_2024-2025_FICTIF.pdf | Procédure : aménagements particuliers pour les examens | all | FICTITIOUS | 1 | 2 502 | 7 | 2026-10-24 | Exam accommodations (not detailed in the official texts) |
| D1-006 | procedure_certificats-releves-de-notes_2024-2025_FICTIF.pdf | Procédure : certificats de scolarité, relevés de notes et diplôme | all | FICTITIOUS | 1 | 2 111 | 6 | 2026-10-24 | Administrative documents and delays (request catalogue REQ-01/02) |
| D1-007 | procedure_depot-soutenance-pfe_2024-2025_FICTIF.pdf | Procédure : dépôt du rapport et soutenance du PFE | all | FICTITIOUS | 2 | 3 137 | 8 | 2026-10-24 | PFE deposit and defence for the three regimes |
| D1-008 | procedure_reclamation-revision-note_2024-2025_FICTIF.pdf | Procédure : réclamation et révision de note | all | FICTITIOUS | 2 | 3 015 | 8 | 2026-10-24 | Grade review (double correction) details |
| D1-009 | procedure_report-annulation-inscription_2024-2025_FICTIF.pdf | Procédure : report et annulation d'inscription | jour;soir | FICTITIOUS | 1 | 2 566 | 6 | 2026-10-24 | Registration postponement / cancellation and refunds |
| D1-010 | guide_stages_2024-2025_FICTIF.pdf | Guide pratique des stages (hors PFE) | jour | FICTITIOUS | 2 | 2 979 | 8 | 2026-10-24 | Internship agreement, supervision and deposit |
| D1-011 | reglement_interieur-vie-campus_2024-2025_FICTIF.pdf | Règlement intérieur : vie sur le campus | all | FICTITIOUS | 2 | 3 885 | 9 | 2026-10-24 | Campus life, support unit (cellule d'écoute), discipline overview |
| D1-012 | guide_frais-scolarite-paiements_2026-2027_FICTIF.pdf | Guide : paiement des frais de scolarité et échéanciers | all | FICTITIOUS | 2 | 3 124 | 8 | 2026-10-26 | Payment methods, instalments, payment-plan request (REQ-19), receipts, late payment — **no amounts** |
| D1-013 | guide_mobilite-internationale_2026-2027_FICTIF.pdf | Guide : mobilité internationale (échange et double diplôme) | all | FICTITIOUS | 2 | 3 155 | 8 | 2026-10-26 | Exchange semester, double degree, application file (REQ-17), selection, learning agreement — internships abroad excluded |

## Why this corpus fits
- It contains **all three official regulations** (one per regime: jour, soir, alternance). The rules really differ by regime
  (e.g. absence justification: day — medical certificate not accepted; evening / work-study — notify within 48 h), so
  `regime` is stored on every document and chunk (ADR-017).
- Every scope topic is covered: exams, retakes, absences, grading, internships and PFE, discipline, registration.
- The FICTITIOUS procedures make deadlines, forms and documents explicit (what students actually ask about) and were
  checked against the official texts (CF-108b: 4 conflicts corrected, 16 overlaps consistent). **Precedence rule (A2):** when
  an official and a FICTITIOUS document disagree, the official one wins; FICTITIOUS content is never presented as an
  official ESPRIT rule — every FICTITIOUS chunk starts with `[DOCUMENT FICTIF — projet CampusFlow AI, non officiel]`.

## Limits
- 13 documents is below the course's 20–60 guideline: the 3 public regulations we could obtain + 10 FICTITIOUS procedures.
  The promised second delivery (finance, mobility) never arrived; D1-012/013 replace it and are written to stay
  consistent with the official texts and the tables (FIN, MOB, REQ-17, REQ-19).
- FICTITIOUS share: 10 of 13 documents but only 26 % of the characters (32 857 of 127 766).
- Rules are those of 2024-2025; the calendar is projected to 2026-2027 (`data/tables/exam_calendar.csv`, `data_status`).
- Four tables of D1-001 were serialised by hand because automatic extraction mixed their cells (`scripts/corpus/manual_tables.json`).
- Excluded: a duplicate day regulation, the exam charter (contained in D1-001) and a 2011-2012 PFE procedure with personal
  e-mail addresses (`data/raw/excluded/`, git-ignored).
