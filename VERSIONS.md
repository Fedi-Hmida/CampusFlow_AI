# Pinned versions

Rule: every image and model is pinned to an exact tag; no floating tags. Recorded on 24 Oct 2026.

## Docker images
| Service | Image | Tag | Digest |
|---|---|---|---|
| n8n | `n8nio/n8n` | `2.44.6` | `sha256:d02752c6ab446ae9db8deec2f9cc887c378f77cdcad31650814df936b7386dfb` |
| qdrant | `qdrant/qdrant` | `v1.20.0` | `sha256:9bfc89f9914fc14876a88c05270685921a55b8877b254a98bcc1cc2f0a424cd2` |
| ollama | `ollama/ollama` | `0.40.10` | `sha256:4c5b27871a3239a717048f9b93057680a51b60c8119a7016aebb57f938e25e35` |
| ngrok | `ngrok/ngrok` | `3.39.13-alpine` | `sha256:a51a7637a70be573615b01852af0419c4ab9dc857601b3d61ea2a082be3ec0d3` |

## Models (Ollama)
| Model | Tag | ID | Size | Use |
|---|---|---|---|---|
| Qwen3 4B Instruct 2507, Q4_K_M | `qwen3:4b-instruct-2507-q4_K_M` | `0edcdef34593` | 2.5 GB | Agent LLM candidate on CPU laptops (ADR-008) |
| Qwen3 8B, Q4_K_M | `qwen3:8b` | `500a1f067a9f` | 5.2 GB | Agent LLM candidate on GPU laptops (ADR-008) |
| BGE-M3 (567M, F16) | `bge-m3:567m` | `790764642607` | 1.2 GB | Embeddings, 1,024 dimensions |

Note: `qwen3:4b` (without suffix) is the thinking-only 2507 model — it ignores `think: false`. Do not use it for agents.

## Measured speed (reference machine, CPU only)
French one-sentence answer, `think: false`, second run (model warm):

| Model | Generation | Prompt processing | Wall time | RAM in container (with bge-m3) |
|---|---|---|---|---|
| `qwen3:4b-instruct-2507-q4_K_M` | 8.7 tokens/s | 248 tokens/s | 8.3 s | 6.3 GiB / 9 GiB |
| `qwen3:8b` | 4.5 tokens/s | 177 tokens/s | 14.3 s | 8.4 GiB / 9 GiB |

## Reference machine
| Item | Value |
|---|---|
| OS | Windows 11 Home Single Language |
| CPU | Intel Core i5-1135G7 (4 cores / 8 threads) |
| RAM | 24 GB (Docker VM: 12 GB + 8 GB swap, 8 CPUs) |
| GPU | NVIDIA GeForce MX330 2 GB (not used — CPU-only, ADR-007) |
| Docker | Docker Desktop 29.4.2 (client and server), WSL2 kernel 6.18.33.2 |
| Ollama runtime | `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_CONTEXT_LENGTH=8192`, `OLLAMA_MAX_LOADED_MODELS=2` |
