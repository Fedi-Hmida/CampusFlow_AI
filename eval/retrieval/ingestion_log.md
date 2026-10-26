# Ingestion log — WF-1 (CF-015 / CF-017)

Checked 2026-10-26 by `scripts/index/verify_index.py` against `data/index/chunks_*.json`. WF-1 run time: 5 min 28 s (embedding on CPU, batches of 16).

| Collection | Strategy | Chunks in file | Points in Qdrant | Same ids | Payload fields + keys | Vectors |
|---|---|---:|---:|---|---|---|
| `regs_fixed` | A | 77 | 77 | ✅ | ✅ | 1024 · Cosine |
| `regs_structured` | B | 168 | 168 | ✅ | ✅ | 1024 · Cosine |

**Result: OK — Qdrant matches the chunk files exactly.**
