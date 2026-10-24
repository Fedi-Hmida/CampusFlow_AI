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
_Filled in at the end of Phase 0._
