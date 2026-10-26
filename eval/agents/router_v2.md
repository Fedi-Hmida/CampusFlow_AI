# Router v2 — compact output + 11 targeted examples (CF-010)

Same dev set, model and protocol as [router_v1.md](router_v1.md) (57 D5 rows, qwen3 4B, temperature 0, schema as
structured output). Changes from v1 ([P-ROUTER-001](../../prompts/P-ROUTER-001.md)): compact schema (entities only when
present; agents derived by n8n), 11 examples chosen from the measured v1 errors
([router_examples_v2.json](../../prompts/examples/router_examples_v2.json)), explicit rules for the regime, own data and
« send it for me ». Raw: `router_results/v2_few.json` (with Ollama counters).

| Metric | v1 few-shot (30 examples) | **v2 (11 examples, compact)** |
|---|---:|---:|
| Intents exactly right | 46 / 57 | **51 / 57** |
| Intent overlap (Jaccard) | 0.83 | **0.91** |
| Valid JSON / schema-valid | 57 / 57 | 57 / 57 |
| Regime invented / missed | 0 / 2 | 1 / 2 |
| Out-of-scope precision / recall | 1.00 / 0.60 | 1.00 / **0.80** |
| Seconds per call (model time) | 52.8 (wall) | **10.0** (2.5 prompt + 7.5 output) |
| Output tokens | — | 37 |

- **Speed:** the static prefix (system prompt + examples, ≈ 1 250 tokens) is read once, then served from Ollama's cache
  (≈ 1 s even when another agent ran in between — [tuning](../latency/tuning_2026-10-26.jsonl)); the shorter output does
  the rest.
- **Fixed:** D5-047 (« ma note en Probabilités ») is now out of scope.
- **Remaining 6:** D5-049 « envoie un email de ma part » → admin **by design** (Admin drafts, never sends; the D5 label says
  out of scope); D5-020 / 041 extra admin intent; D5-009 / 033 calendar vs regulations on retake dates; D5-051 (duplicata
  cost) → regulations. 1 invented regime (D5-026). Labels are unverified (Fedi's review pending).
- **Leak found after the run (fixed):** example R22 (inherited from v1) shared 6 words with dev row D5-020; v1 few-shot
  and v2 were measured with it. No inflation: D5-020 counts as a miss in both. The example is rephrased and the
  validator now checks Router examples against T1–T5 **and** the D5 dev rows.
