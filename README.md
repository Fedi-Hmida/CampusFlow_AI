# CampusFlow AI

Telegram assistant for ESPRIT students: regulation questions (RAG with citations), exam dates, administrative contacts
and request drafts, plus photo understanding (convocations, notices, timetables). Multi-agent workflows in n8n, local
models in Ollama, vectors in Qdrant — all in Docker; image reading and the long-writing agents use Gemini Flash-Lite
(per-agent hybrid for the 90 s latency target — ADR-010, switch in `config/agents.json`).

Final project — Advanced DL (DS14), ESPRIT 2026–2027 · Team: Fedi, Doua, Ines · Exact versions: [VERSIONS.md](VERSIONS.md)

## Repository layout
| Path | Content |
|---|---|
| `docker-compose.yml` | n8n + Qdrant + Ollama + ngrok on network `campusflow-net` |
| `.env.example` | variables to copy into `.env` (never commit `.env`) |
| `VERSIONS.md` | pinned images, models, measured speeds |
| `workflows/` | exported n8n workflows (JSON) |
| `data/raw/` | team delivery, byte-for-byte (checksums in `data/raw/MANIFEST.md`) — never edited |
| `data/regs/` | `official/` (3 regulations) · `fictitious/` (8 labelled `*_FICTIF.pdf`) · `clean/` (text + article index) · `CORPUS_CARD.md` |
| `data/tables/` | exam calendar, module codes, directory, request catalogue (CSV) |
| `scripts/` | `run_all.py` rebuilds every data output and validates it; `lib/` · `corpus/` · `tables/` · `testsets/` (see `scripts/README.md`) |
| `eval/` | `testsets/` (T1–T5, `T4_photos/`) · `review/` (`sheets/`, `ticks/`, `verified/`) · `retrieval/` (metrics + notebook) · `agents/` (tool test, Vision prompt eval) · `latency/` · `baselines/` · `candidates/` (D5 — **not** a test set) |
| `prompts/` · `diagrams/` · `report/` | prompt library (`P-<AGENT>-001.md`, `schemas/`, `examples/`, `archive/`) · architecture diagrams and org chart · technical report |

## 1. Prerequisites
- Windows 10/11 with **Docker Desktop (WSL2 backend)**, or Linux with Docker Engine; **Git**.
- **16 GB RAM minimum** (24 GB comfortable), ~15 GB free disk for images and models.
- Free accounts: **Telegram** (bot via @BotFather), **ngrok** (free dev domain), **Google AI Studio** (Gemini API key).

## 2. Docker memory (Windows)
Create `%UserProfile%\.wslconfig`:
```ini
[wsl2]
memory=12GB
swap=8GB
processors=8
```
Then `wsl --shutdown`, restart Docker Desktop, and check `docker info --format '{{.MemTotal}}'` (≈ 12.5e9).

## 3. Environment file
```powershell
Copy-Item .env.example .env
# generate the n8n encryption key ONCE and paste it after N8N_ENCRYPTION_KEY= in .env
$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b)
```
- **Back the key up** (password manager). n8n encrypts every saved credential with it: if it changes or is lost,
  all credentials become unreadable and must be re-entered.
- Set `WEBHOOK_URL=https://<your-domain>.ngrok-free.dev/` and the two `NGROK_*` values (step 6).
- Gemini and Telegram secrets do **not** go in `.env`: they live encrypted in n8n credentials (step 7). The only
  secrets in `.env` are the n8n encryption key and the ngrok authtoken, needed to start the containers.

## 4. Start the stack
```powershell
docker compose up -d
docker compose ps        # n8n, qdrant, ollama, ngrok: Up
```
Python tools (scripts/, eval/): `python -m venv .venv` then `.venv\Scripts\python -m pip install -r requirements.txt`,
then `.venv\Scripts\python scriptsun_all.py` (rebuilds and validates everything; must end with 0 error).

Check: n8n http://localhost:5678 · Qdrant http://localhost:6333/dashboard · Ollama http://localhost:11434/api/version.
Ports are bound to `127.0.0.1` (not reachable from the LAN).

## 5. Pull the models
```powershell
docker compose exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M   # default agent model (CPU)
docker compose exec ollama ollama pull bge-m3:567m                     # embeddings, 1024 dims
docker compose exec ollama ollama pull qwen3:8b                        # optional, GPU laptops only
```
Do not use the plain `qwen3:4b` tag (thinking-only build: ignores `think:false`).

## 6. Public tunnel for Telegram (ngrok)
Telegram delivers messages to a public HTTPS webhook; `localhost` cannot receive them. The `ngrok` service in
`docker-compose.yml` opens that tunnel automatically with `docker compose up -d`. Put in `.env`:
```
NGROK_AUTHTOKEN=<ngrok dashboard → Your Authtoken>
NGROK_DOMAIN=<your-domain>.ngrok-free.dev        # dashboard → Domains (free dev domain)
```
Check: `docker compose logs ngrok` shows `started tunnel … url=https://<your-domain>.ngrok-free.dev`.
Only **one** ngrok agent may serve a domain: do not also run `ngrok http …` on the host.
Fallback without the container: `ngrok http --domain=<your-domain>.ngrok-free.dev 5678`.

## 7. n8n credentials
Open http://localhost:5678, create the owner account (skip the n8n Assistant), then **Overview → Credentials → Create**:

| Credential type | Name | Value |
|---|---|---|
| Ollama | `Ollama (local)` | Base URL `http://ollama:11434` |
| Qdrant | `Qdrant (local)` | URL `http://qdrant:6333`, no API key |
| Google Gemini (PaLM) API | `Google Gemini API` | Host `https://generativelanguage.googleapis.com`, your AI Studio key |
| Telegram | `Telegram CampusFlowAI_bot` | the token from @BotFather |

Use **service names** (`ollama`, `qdrant`), not `localhost`: inside the n8n container, `localhost` is n8n itself.

## 8. Import and test the smoke-test workflow
1. n8n → **Create workflow → ⋯ → Import from File** → `workflows/00_smoke_test.json`.
2. Open each node with a credential (Telegram Trigger, Gemini vision, Reply on Telegram) and select yours.
3. Click **Publish** (top right). Do **not** click *Execute* while it is published (see troubleshooting).
4. In Telegram, open **your bot** (not BotFather), press **Start** and send a question → the reply shows an Ollama
   sentence, a Qdrant score and "no photo attached". Send a photo with a caption → the Gemini line describes it.
   Runs appear in the workflow's **Executions** tab (≈ 15 s cold, ≈ 6 s warm on CPU).

## 9. GPU (stronger laptops)
Ollama runs on CPU by default (reference laptop: NVIDIA MX330, 2 GB VRAM — too small). With an NVIDIA GPU of
≥ 8 GB VRAM, uncomment the `deploy:` block of the `ollama` service and use `qwen3:8b`. Windows needs a recent NVIDIA
driver; Linux needs the NVIDIA Container Toolkit; macOS is CPU only. Check: `docker compose exec ollama ollama ps`
(PROCESSOR `100% GPU`).

## 10. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| An Ollama request takes minutes, container near its memory limit | Ollama sizes itself on the VM RAM, not the container limit, and loads a third model → thrashing | Keep `OLLAMA_MAX_LOADED_MODELS=2` (set in compose); `docker compose exec ollama ollama stop <model>` |
| `docker compose exec … /tmp/x` fails with a `C:/Users/.../Temp/...` path | Git Bash rewrites Unix paths | Prefix the command with `MSYS_NO_PATHCONV=1`, or use PowerShell |
| "Problem running workflow … Telegram Trigger can't listen for test executions" | Telegram allows one webhook per bot; the published workflow already holds it | Don't click *Execute*; message the bot and watch **Executions** (or unpublish to test) |
| Credentials show errors / "could not decrypt" after a reinstall | `N8N_ENCRYPTION_KEY` changed | Restore the original key in `.env`, `docker compose up -d n8n` |
| Bot does not answer | ngrok container down, a second ngrok agent on the same domain, or message sent to BotFather | `docker compose logs ngrok`, `docker compose up -d ngrok`; check `https://api.telegram.org/bot<TOKEN>/getWebhookInfo` (url = your domain, no `last_error_message`) |
| `ngrok http … --url` → "unknown flag" (host fallback) | Old ngrok CLI | Use `--domain=<your-domain>.ngrok-free.dev`, or `ngrok update` |
| `docker compose up` → "Set N8N_ENCRYPTION_KEY / NGROK_AUTHTOKEN / NGROK_DOMAIN in .env" | `.env` missing or incomplete | Steps 3 and 6 |
