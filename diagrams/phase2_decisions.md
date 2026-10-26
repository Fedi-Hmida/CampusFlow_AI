# Phase 2 — knowledge base and tools: decisions (CF-021)

One page for the report and the defence. Every number comes from a committed file (linked).

## 1. Corpus (13 documents)
- 3 official regulations (one per regime) + 10 FICTITIOUS procedures, labelled on every page and every chunk.
- The promised second dataset never arrived; **D1-012 (paying fees) and D1-013 (international mobility)** were written by
  the project, consistent with the directory and the request catalogue, **without tuition amounts and without internships
  abroad**, so the bot still answers « non trouvé » to T1-23 / T1-25 instead of inventing
  ([CORPUS_CARD](../data/regs/CORPUS_CARD.md), [INTAKE](../data/INTAKE.md)).

## 2. Two chunking strategies, one embedding model
| | A — fixed windows | B — articles / sub-sections |
|---|---|---|
| Rule | 2 000 chars (≈ 500 tokens), 200 overlap | one unit per article; > 2 000 chars split at sentence ends, heading repeated |
| Chunks | 77 | 168 |
| Citation | article keys overlapped (≈ 2.8 per chunk) | exact article key (≈ 1 per chunk) |

bge-m3 (1024 dims, cosine) for both; payload = doc, status, regime(s), article keys, pages, text; deterministic point
ids, so re-indexing replaces instead of duplicating ([data/index](../data/index/README.md),
[ingestion log](../eval/retrieval/ingestion_log.md): 77 + 168 points, ids and payloads checked).

## 3. Retrieval decision (T1, 22 answerable questions — [results](../eval/retrieval/results_T1.md))
| | Hit@5 | Recall@5 | Text sent to the model |
|---|---:|---:|---:|
| A, regime filter | 0.86 | 0.82 | 8 843 chars |
| B, regime filter | 0.86 | 0.75 | 4 145 chars |
| **B, official first (3 official + 2 FICTITIOUS)** | **1.00** | **0.93** | 5 297 chars |

- **B**: same hit rate as A with half the text, which matters on a CPU reading ≈ 31 tokens/s.
- **Official first**: the 3 misses were absence questions where the FICTITIOUS absence procedure (written in students'
  words) out-ranked the official « Assiduité » articles; a quota of official chunks fixes them and enforces
  « official beats FICTITIOUS ».
- **Regime filter**: without it A drops to 0.77 → the bot asks for the regime when the rule depends on it.
- **No similarity threshold for « not found »**: best scores of unanswerable questions (up to 0.62) overlap answerable
  ones (from 0.55); the Regulations agent decides from the excerpts.
- Limit: one run, 22 questions, quota chosen on T1 itself → slightly optimistic; confirmed later by full answers.

## 4. Structured data as tools, not vectors
- Exam calendar, directory, request catalogue stay CSV tables; three n8n tool workflows (exam, contact, request) return
  exact rows or `found: false` / `needs_input` — never a guess (« non communiqué » for empty cells).
- The tool code is one file, [workflows/lib/lookup.js](../workflows/lib/lookup.js), tested by 30 Node tests (the 12
  verified T2 rows replayed) and embedded verbatim in n8n; live n8n output = local output on 15/15 queries
  ([tools test](../eval/agents/tools_test.md)). WF-2 checks the three tables (1 560 / 18 / 24 rows, all OK).

## 5. Latency budget (CF-008b — [eval/latency](../eval/latency/README.md))
- 4B model on CPU: 30.7 tok/s prompt, 4.1 tok/s output; the full 5-call chain ≈ 415 s vs the 90 s target.
- Proposed (ADR-010, awaiting approval): short Router output, Composer only for multi-intent questions, Critic as
  deterministic checks + optional LLM, cached static system prompts.

## 6. Security
n8n is reachable through ngrok, so every published webhook is public: test webhooks are published only for a run
and unpublished afterwards; tool workflows have no public URL.
