# CampusFlow AI — Project Memory

**Always read `Docs/` before acting** (start with `Docs/00_Index.md`).

## Summary
CampusFlow AI is a Telegram assistant for ESPRIT students, built as the final project of the Advanced DL course (DS14)
by Fedi, Doua and Ines. It answers questions about regulations (RAG over PDFs, with citations), exam dates and
administrative contacts (exact lookup tools), and helps prepare administrative requests. An orchestrator–worker
multi-agent system in n8n (Router → Vision / Regulations / Calendar / Admin → Composer → Critic) uses versioned prompts
and reads photos of notices and timetables. Everything runs locally in Docker except image reading (Gemini Flash-Lite).

## Stack
- Docker Compose, network `esa-net` (or `campusflow-net`): **n8n** 2.x · **Qdrant** 1.x · **Ollama** (Qwen3 8B 4-bit + bge-m3)
- Gemini Flash-Lite (vision; fallback Qwen2.5-VL 3B) · Telegram Bot API · ngrok (webhook)
- Evaluation: Python 3.11+, Jupyter, qdrant-client, pandas
- All versions pinned in `VERSIONS.md`

## Folder map
```
CLAUDE.md           this file
README.md           run instructions
VERSIONS.md         pinned versions
docker-compose.yml  n8n + Qdrant + Ollama
.env.example        variable names only, no secrets
workflows/          exported n8n JSON (WF-1..WF-4)
data/raw/           team delivery, byte-for-byte (never edit; excluded/ is git-ignored)
data/regs/          official/ (3 PDFs) · fictitious/ (8 *_FICTIF.pdf) · clean/ (D1-*.json) · CORPUS_CARD.md
data/tables/        calendar, module codes, directory, request catalogue CSVs (D2-D4) · data/INTAKE.md (new data)
scripts/            run_all.py · validate_data.py · lib/ · corpus/ · tables/ · testsets/ (see scripts/README.md)
prompts/            prompt library: P-<AGENT>-001.md (versions inside) · schemas/ · examples/ · archive/
eval/               testsets/ (T1-T5 + T4_photos/) · review/{sheets,ticks,verified}/ · retrieval/ · agents/
                    · latency/ · baselines/ · candidates/ (D5, NOT a test set)
diagrams/           PUBLIC diagrams for the report (committed)
report/             final report
Docs/               PRIVATE (git-ignored): reference/ · planning/ · decisions/ · reports/ (index: Docs/00_Index.md)
```
Rebuild all data outputs: `.venv/Scripts/python scripts/run_all.py` (ends with the validator).

## Working rules
- Read `Docs/` before any task; follow the spec book and action plan; if a request conflicts with them, say so.
- Never commit `Docs/` or `.env`. Never print, read aloud or commit secrets (API keys, tokens).
- Ask before `git push`, before deleting files, and before any destructive Docker command.
- One branch per ticket (e.g. `cf-002-docker-compose`); commit messages start with the ticket ID (`CF-002: ...`).
- **No Claude attribution in Git**: no `Co-Authored-By: Claude`, no "🤖 Generated with Claude Code" line, no Claude
  icon or mention in commit messages, PR titles or PR bodies.
- Pin every version; no `latest` image tags.
- After each ticket: verify the acceptance criteria, update the progress tracker in `Docs/planning/03_Action_Plan.md`,
  and note anything useful for the final report in `Docs/decisions/04_Decisions_Log.md`.
- When a step needs a human action (GUI, account creation, secrets), stop and give a clear checklist.

## Conventions
- Export workflows to `workflows/` after each session; merge after review.
- Definition of Done: acceptance criteria checked by another member; workflow exported or file committed;
  decision written down for the report.
- Agents output JSON (router, vision, critic, specialists); Composer outputs text. Temperature 0–0.2, Composer 0.3.
- Never invent rules, dates or contacts: "not found" + right office.
