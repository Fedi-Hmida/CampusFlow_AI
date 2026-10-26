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
