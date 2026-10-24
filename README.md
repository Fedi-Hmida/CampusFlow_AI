# CampusFlow AI

Telegram assistant for ESPRIT students: regulations (RAG with citations), exam calendar, administrative contacts and
request drafts, with photo understanding. Built on n8n, Qdrant and Ollama in Docker (vision on Gemini Flash-Lite).

Final project — Advanced DL (DS14), ESPRIT 2026–2027 · Team: Fedi, Doua, Ines.

## Repository layout
| Path | Content |
|---|---|
| `docker-compose.yml` | n8n + Qdrant + Ollama stack |
| `.env.example` | environment variable names (copy to `.env`, never commit `.env`) |
| `VERSIONS.md` | pinned versions of every image and model |
| `workflows/` | exported n8n workflows (JSON) |
| `data/regs/` | regulation PDFs |
| `data/tables/` | calendar, directory and request catalogue (CSV) |
| `prompts/` | versioned prompt library |
| `eval/` | test sets and retrieval evaluation |
| `diagrams/` | architecture diagrams for the report |
| `report/` | technical report |

## Setup
_Full instructions are filled in at the end of Phase 0._

### Docker memory & GPU
**Windows (WSL2):** create `%UserProfile%\.wslconfig`:
```ini
[wsl2]
memory=12GB
swap=8GB
processors=8
```
Then `wsl --shutdown` and restart Docker Desktop. Check with `docker info --format '{{.MemTotal}}'` (≈ 12.5e9).

**GPU:** the compose file runs Ollama on CPU (reference laptop: NVIDIA MX330, 2 GB VRAM — too small for the models).
On a machine with an NVIDIA GPU with ≥ 8 GB VRAM, uncomment the `deploy:` block of the `ollama` service.
Windows needs a recent NVIDIA driver (WSL2 GPU support); Linux needs the NVIDIA Container Toolkit; macOS is CPU only.
Check with `docker compose exec ollama ollama ps` (PROCESSOR column: `100% GPU` or `100% CPU`).
