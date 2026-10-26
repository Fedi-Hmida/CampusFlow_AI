# Latency (CF-008b)

Script: [latency_benchmark.py](latency_benchmark.py) — RAG-sized prompt (≈ 2 100 tokens, unique nonce so the prompt
cache is not reused), 250 output tokens, 3 runs. Raw results: [results_2026-10-26.jsonl](results_2026-10-26.jsonl).

## 26 Oct 2026 — `qwen3:4b-instruct-2507-q4_K_M`, CPU only (reference laptop, Docker VM 12.5 GB / 8 CPUs)
| Run | Prompt tokens | Prefill | Output tokens | Generation | Total |
|---|---:|---:|---:|---:|---:|
| 1 | 2 136 | 66.7 s (32.0 tok/s) | 250 | 58.1 s (4.30 tok/s) | 126.9 s |
| 2 | 2 137 | 72.6 s (29.4 tok/s) | 250 | 59.3 s (4.22 tok/s) | 134.3 s |
| 3 | 2 138 | 69.4 s (30.8 tok/s) | 250 | 64.4 s (3.88 tok/s) | 136.3 s |
| **Mean** | | **30.7 tok/s** | | **4.13 tok/s** | **132.5 s** |

Generation on a long prompt is half the 8.7 tok/s measured on a one-sentence prompt in CF-004.

## Consequence for one student question (script estimate, 5 LLM calls)
| Step | Prompt / output tokens | Seconds |
|---|---|---:|
| Router | 600 / 80 | 38.9 |
| Regulations | 2 500 / 250 | 141.8 |
| Calendar / Admin | 800 / 150 | 62.3 |
| Composer | 1 200 / 250 | 99.5 |
| Critic | 1 500 / 100 | 73.0 |
| **Total** | | **≈ 415 s** |

NFR-01 asks ≤ 90 s → the full 5-LLM chain is **4.6× over budget** on this laptop. Design response: ADR-010
(token budget per agent, Composer merged into the specialist for single-intent questions, Critic as deterministic
checks + optional LLM, cached static system prompts).

## 26 Oct evening — CF-010: the latency decision (ADR-010), measured
All scripts and raw files in this folder; per-flow table: [budget.md](budget.md) (`budget.py`, tested by `budget_test.py`).

| Lever | Measurement | Result |
|---|---|---|
| Threads | `tuning_bench.py` — num_thread 4 vs 8 (i5-1135G7, 4 cores / 8 threads) | prompt 35.8–39.9 vs 35.6–36.9 tok/s → **no gain**, keep the default |
| Prompt-prefix cache | same static prefix, 3 calls | 37.4 s → **0.9 s / 1.2 s** to read 1 234 tokens |
| Cache when agents alternate | Router → Router → Regulations → Router | Router prefix still cached after a Regulations call: **1.0 s** |
| Retrieval | bge-m3 embedding + 2 Qdrant queries | **0.08 s** |
| Router v2 | 57 D5 rows ([router_v2.md](../agents/router_v2.md)) | **10.0 s** (was 52.8 s) and more accurate (51 / 57) |
| Regulations v2, local | 10 T1 questions, 5 chunks, ≤ 160 tokens ([regulations_2026-10-26.jsonl](regulations_2026-10-26.jsonl)) | **103 s** model time (45–84 s reading 1 640–2 600 tokens) |
| Regulations v2, Gemini | 3 T1 questions, same context ([gemini_2026-10-26.jsonl](gemini_2026-10-26.jsonl)) | **4.6–8.8 s** wall (incl. n8n + host overhead) |

**Measurement artefact found and fixed:** on this Windows host `http://localhost` costs ≈ 2 s per request (IPv6 attempt
first); `127.0.0.1` costs 3 ms. All evaluation scripts now use 127.0.0.1; local agent times above are Ollama counters
(model time). n8n uses Docker service names and does not pay this.

**Quality seen on the way (10 local + 3 Gemini answers, not an evaluation):** local cites the expected article on 8 / 8
answerable questions; the deterministic checks caught 2 missing FICTIF labels and 1 « not found » without contact; **one
invented rule passed the checks** (T1-25: « ne peut pas être effectué à l'étranger », absent from D1-001/7-9). Gemini
missed one answerable question (T1-13 « non trouvée »). → T1 through WF-3 (Phase 4) decides quality.

**Decision (ADR-010):** per-agent hybrid — local Router, tools, embeddings, checks; Gemini Flash-Lite for the three
long-writing agents (Regulations, Admin draft, Composer); `config/agents.json` `mode` switches back to fully local.
