# CampusFlow AI — architecture (CF-014)

State on 26 Oct 2026. Solid boxes exist and are tested; dashed boxes are planned (Phase 4–7). The conditional Composer
and the deterministic Critic follow the latency budget proposed in ADR-010 (CPU: 30.7 tok/s prefill, 4.1 tok/s output).

```mermaid
flowchart LR
  student([Student · Telegram]) -->|message / photo| ngrok[ngrok tunnel]
  ngrok --> wf3

  subgraph wf3 [WF-3 assistant · n8n — planned]
    direction LR
    router[Router\nqwen3 4B · JSON]:::planned
    vision[Vision\nGemini Flash-Lite · JSON\nprompt v4]:::planned
    regs[Regulations\nqwen3 4B · RAG]:::planned
    cal[Calendar]:::planned
    adm[Admin]:::planned
    comp[Composer\nmulti-intent only]:::planned
    critic[Critic\nchecks + optional LLM]:::planned
    router -->|photo| vision
    router --> regs & cal & adm
    vision --> regs & cal
    regs & cal & adm --> comp --> critic
  end
  critic -->|reply / one revision / escalate| student

  subgraph kb [Knowledge base · built]
    clean[(data/regs/clean\n13 documents)] --> chunks[[build_chunks.py\nA 77 · B 168]]
    chunks --> wf1[WF-1 index\nbge-m3 · 1024 d]
    wf1 --> qA[(Qdrant regs_fixed · A)]
    wf1 --> qB[(Qdrant regs_structured · B)]
  end
  regs -->|top-k, regime filter| qA & qB

  subgraph tools [Lookup tools · built]
    t10[10 lookup_exam] --> csvc[(exam_calendar.csv)]
    t11[11 lookup_contact] --> csvd[(directory.csv)]
    t12[12 lookup_request] --> csvr[(request_catalogue.csv)] & csvd
    wf2[WF-2 tables check] --> csvc & csvd & csvr
  end
  cal --> t10
  adm --> t11 & t12

  wf4[WF-4 errors + logs]:::planned -.-> wf3
  classDef planned stroke-dasharray: 5 5
```

| Part | Technology | Status | Evidence |
|---|---|---|---|
| Channel | Telegram bot + ngrok static domain | working (smoke test) | `workflows/00_smoke_test.json` |
| Router, specialists, Composer, Critic | n8n + Ollama qwen3 4B, prompts `prompts/P-*-001.md`, schemas `prompts/schemas/` | prompts + schemas ready; Router measured (CF-022) | `eval/agents/router_v1.md` |
| Vision | Gemini Flash-Lite, prompt v4 | measured 87/88 fields on T4 | `eval/agents/vision_v1_to_v4.md` |
| Regulations KB | 13 docs → chunks A/B → bge-m3 → Qdrant | indexed (WF-1) | `eval/retrieval/ingestion_log.md` |
| Tables | 3 CSV + tools 10–12 + WF-2 | tested (30 node tests + live run) | `eval/agents/tools_test.md` |
| Latency | CPU only | measured, budget proposed | `eval/latency/README.md`, ADR-010 |
