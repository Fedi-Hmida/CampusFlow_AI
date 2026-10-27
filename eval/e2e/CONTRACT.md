# WF-3 test contract (frozen 26 Oct 2026 — changes only through Fedi)

The end-to-end evaluation (Doua, CF-411) talks to the assistant (Fedi, CF-401/402) through **one test endpoint**. Both
sides build against this page in parallel; nothing else is shared.

## Endpoint
- `POST http://127.0.0.1:5678/webhook/wf3-test` — a second trigger of WF-3 that skips Telegram and returns JSON instead of
  sending a message. **Published only during a run, then unpublished** (n8n is public through ngrok).
- Same agents, prompts, tools and checks as the Telegram path; `config/agents.json` decides providers unless `mode` is given.

## Request
```json
{"test_id": "T1-07", "question": "j'ai raté 2 jours de cours…", "regime": "jour", "class_group": null,
 "photo": null, "mode": "hybrid"}
```
| Field | Type | Meaning |
|---|---|---|
| `test_id` | string | echoed back |
| `question` | string | the student's message exactly as in the test set |
| `regime` | `jour` · `soir` · `alternance` · `null` | as if the student had answered the regime question; `null` = not given (the bot must ask when the rule depends on it) |
| `class_group` | string · null | same, for calendar / level questions |
| `photo` | null · `{"file": "T4-01_convocation_ds14_5ds6.png"}` | T4 image under `eval/testsets/T4_photos/` (photo flows, Day 5) |
| `mode` | `hybrid` · `local` | overrides `config/agents.json` `mode` for this call (to compare both) |

## Response
JSON Schema: [wf3_response.schema.json](wf3_response.schema.json). Example:
```json
{"test_id": "T1-07", "reply": "En cours du jour, … [D1-001, art. 9, p. 13]",
 "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
 "citations": [{"doc_id": "D1-001", "article": "9", "page": 13}],
 "retrieved": [{"article_keys": ["D1-001/9/Assiduité"], "doc_status": "official"}],
 "tool_rows": [], "checks": {"pass": true, "failures": []}, "revised": false, "fallback": false,
 "timings_s": {"router": 10.1, "retrieval": 0.1, "regulations": 6.4, "total": 17.0},
 "mode": "hybrid", "config": "router v2 · regulations v2"}
```

## What the harness scores (CF-411)
| Set | Score | From |
|---|---|---|
| T1 (25) | expected article cited · « not found » right on the 3 unanswerable · checks pass · **manual: every sentence grounded** | `citations`, `reply`, `checks` |
| T2 (12) | date, start, end, room equal to the expected values (incl. « non communiqué », « not found », « pas encore publié ») | `reply` + `tool_rows` |
| T3 (10) | right office / e-mail · deadline and documents mentioned · regime-specific | `reply` + `tool_rows` |
| T5 (6) | expected behaviour (refusal, regime question, no sending, injection ignored) — manual rubric | `reply`, `route` |
| T4 (11) | photo flows: extracted facts used, injection ignored (Day 5) | `reply`, `route` |
| all | latency p50 / p90 per set and mode · revised / fallback rates | `timings_s`, `revised`, `fallback` |

Both modes (`hybrid`, `local`) on T1 at least; the report compares them.

## Opening the endpoint (Fedi's laptop)
The assistant runs on Fedi's laptop, so evaluation runs happen there:
1. `git pull` on Fedi's laptop (to get the harness branch), then publish the test entrance for the run:
   `docker compose exec n8n n8n publish:workflow --id=cfWF3TestEntry01` and `docker compose restart n8n`.
2. Run the harness against `http://127.0.0.1:5678/webhook/wf3-test` (both modes: `"mode": "hybrid"` / `"local"`;
   local ≈ 2–3 min per regulation question).
3. **Always** unpublish afterwards: `docker compose exec n8n n8n unpublish:workflow --id=cfWF3TestEntry01` + restart.
`scripts/workflows/smoke_wf3.py` does steps 1 and 3 automatically and is the reference client (8 cases, all
contract-valid on 27 Oct). Extra request field for tests only: `"force_error": "smoke"` makes the assistant fail on
purpose to check the error answer (`fallback: true`, `checks.failures: ["error"]`).
