"""CF-120 — set up the whole platform on a new laptop with one command (teammates, demo machine, rebuild after a reset).

  1. checks .env and Docker            5. imports the workflows (fixed ids) and publishes the production ones
  2. starts n8n, Qdrant, Ollama        6. indexes the regulations into Qdrant (WF-1) when the collections are missing
  3. pulls the two models              7. checks everything and prints what to do next
  4. creates the n8n credentials with the ids the workflows expect (secrets typed, never stored or printed)

Run (repo root): .venv/Scripts/python -X utf8 scripts/setup/bootstrap.py [--gemini] [--telegram]
  --gemini     ask for YOUR Gemini API key (needed in hybrid mode, the default in config/agents.json)
  --telegram   also start ngrok and set up YOUR OWN Telegram bot (needs NGROK_* + WEBHOOK_URL in .env)
Safe to re-run: every step checks first. It never prints a secret and refuses the team bot's token on another laptop.
Guide: team/RUN_THE_PLATFORM.md
"""
import argparse
import getpass
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
N8N_URL = "http://127.0.0.1:5678"
QDRANT_URL = "http://127.0.0.1:6333"
OLLAMA_URL = "http://127.0.0.1:11434"
MODELS = ["qwen3:4b-instruct-2507-q4_K_M", "bge-m3:567m"]
COLLECTIONS = {"regs_structured": 168, "regs_fixed": 77}
TEAM_BOT = "CampusFlowAI_bot"   # Fedi's bot: one webhook per bot, so another laptop must never take its token
CREDS = {"gemini": {"id": "cfGeminiApi00001", "name": "Google Gemini API", "type": "googlePalmApi"},
         "telegram": {"id": "cfTelegramBot001", "name": "Telegram bot", "type": "telegramApi"}}
IMPORT = ["10_tool_lookup_exam", "11_tool_lookup_contact", "12_tool_lookup_request", "20_llm_call", "03_wf3_assistant",
          "04_wf4_errors", "03b_wf3_test", "01_wf1_index_regs", "02_wf2_tables_check"]
PUBLISH = ["cfToolExam000001", "cfToolContact001", "cfToolRequest001", "cfLLMCall0000001", "cfWF3Assistant01",
           "cfWF4Errors00001"]
TEST_ENTRANCE, TELEGRAM_ENTRY, WF1 = "cfWF3TestEntry01", "cfWF3Telegram001", "cfWF1IndexRegs01"
ENV = {**os.environ, "MSYS_NO_PATHCONV": "1"}   # Git Bash would rewrite /tmp/... paths


def step(msg: str) -> None:
    print(f"\n== {msg}", flush=True)


def fail(msg: str) -> None:
    sys.exit(f"\n✗ {msg}")


def run(args: list[str], check: bool = True, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(args, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if check and r.returncode != 0:
        fail(f"{' '.join(args[:6])} … failed:\n{(r.stderr or r.stdout)[-800:]}")
    return r


def n8n(*args: str, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    extra = [x for k, v in (env or {}).items() for x in ("-e", f"{k}={v}")]
    return run(["docker", "compose", "exec", "-T", *extra, "n8n", "n8n", *args], check=check)


def get_json(url: str, timeout: float = 10) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def wait_for(url: str, what: str, seconds: int = 180) -> None:
    for _ in range(seconds // 3):
        try:
            urllib.request.urlopen(url, timeout=5)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(3)
    fail(f"{what} did not answer at {url} after {seconds} s — see `docker compose logs`")


def env_values() -> dict:
    """Names → whether set. Values are read only to check presence and are never printed."""
    path = ROOT / ".env"
    if not path.exists():
        fail(".env is missing: copy .env.example to .env and fill N8N_ENCRYPTION_KEY (team/RUN_THE_PLATFORM.md, step 3)")
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def preflight(telegram: bool) -> None:
    step("1/7 Checks")
    env = env_values()
    if not env.get("N8N_ENCRYPTION_KEY"):
        fail("N8N_ENCRYPTION_KEY is empty in .env (generate it once, keep a copy: team/RUN_THE_PLATFORM.md, step 3)")
    for k in ("NGROK_AUTHTOKEN", "NGROK_DOMAIN", "WEBHOOK_URL"):
        if not env.get(k):
            fail(f"{k} is empty in .env — without Telegram, put any placeholder (see .env.example and the guide)")
    if telegram and ("localhost" in env["WEBHOOK_URL"] or "ngrok" not in env["WEBHOOK_URL"]):
        fail("--telegram needs WEBHOOK_URL=https://<your-domain>.ngrok-free.dev/ in .env (your own ngrok domain)")
    if run(["docker", "info"], check=False).returncode != 0:
        fail("Docker is not running: start Docker Desktop and retry")
    print("✓ .env complete, Docker running")


def start(telegram: bool) -> None:
    step("2/7 Start the containers")
    run(["docker", "compose", "up", "-d", "n8n", "qdrant", "ollama", *(["ngrok"] if telegram else [])])
    wait_for(f"{N8N_URL}/healthz", "n8n")
    wait_for(f"{QDRANT_URL}/healthz", "Qdrant")
    wait_for(f"{OLLAMA_URL}/api/version", "Ollama")
    print("✓ n8n, Qdrant, Ollama up" + (", ngrok started" if telegram else " (ngrok left as it is: no --telegram)"))


def models() -> None:
    step("3/7 Models (≈ 3.7 GB the first time)")
    have = {m["name"] for m in (get_json(f"{OLLAMA_URL}/api/tags") or {}).get("models", [])}
    for m in MODELS:
        if m in have:
            print(f"✓ {m} already there")
            continue
        print(f"… pulling {m} (several minutes)", flush=True)
        run(["docker", "compose", "exec", "-T", "ollama", "ollama", "pull", m], timeout=3600)
        print(f"✓ {m}")


def owner_exists() -> bool:
    s = get_json(f"{N8N_URL}/rest/settings") or {}
    return not (s.get("data", s).get("userManagement", {}).get("showSetupOnFirstLoad", False))


def credential_exists(cid: str) -> bool:
    return n8n("export:credentials", f"--id={cid}", check=False).returncode == 0


def telegram_bot_name(token: str) -> str | None:
    me = get_json(f"https://api.telegram.org/bot{token}/getMe")
    return me["result"]["username"] if me and me.get("ok") else None


def credentials(gemini: bool, telegram: bool, replace: bool, team_laptop: bool) -> None:
    step("4/7 Credentials (typed here, encrypted by n8n, never written in the repo)")
    if not owner_exists():
        fail(f"n8n has no owner account yet: open {N8N_URL}, create it (your e-mail + a strong password), then re-run")
    todo = []
    if gemini:
        if credential_exists(CREDS["gemini"]["id"]) and not replace:
            print("✓ Gemini credential already there (--replace-credentials to change it)")
        else:
            key = getpass.getpass("Your Gemini API key (Google AI Studio → Get API key; input hidden): ").strip()
            if not key:
                fail("empty Gemini key")
            todo.append({**CREDS["gemini"], "data": {"host": "https://generativelanguage.googleapis.com", "apiKey": key}})
    else:
        print("· no Gemini key asked (--gemini): hybrid mode needs it; local mode does not (config/agents.json)")
    if telegram:
        if credential_exists(CREDS["telegram"]["id"]) and not replace:
            print("✓ Telegram credential already there (--replace-credentials to change it)")
        else:
            token = getpass.getpass("YOUR bot token from @BotFather (input hidden): ").strip()
            name = telegram_bot_name(token)
            if not name:
                fail("Telegram rejected this token (getMe failed): copy it again from @BotFather")
            if name == TEAM_BOT and not team_laptop:
                fail(f"@{TEAM_BOT} is the team bot served by Fedi's laptop. A bot has ONE webhook: using its token here "
                     f"would take the bot away from the demo laptop. Create your own bot with @BotFather (/newbot).")
            print(f"✓ token belongs to @{name}")
            todo.append({**CREDS["telegram"], "name": f"Telegram {name}", "data": {"accessToken": token}})
    if not todo:
        return
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(todo, f)
        run(["docker", "compose", "cp", tmp, "n8n:/tmp/cf_creds.json"])
        n8n("import:credentials", "--input=/tmp/cf_creds.json")
    finally:
        run(["docker", "compose", "exec", "-T", "n8n", "rm", "-f", "/tmp/cf_creds.json"], check=False)
        os.remove(tmp)
    print(f"✓ {len(todo)} credential(s) imported with the ids the workflows use; temporary files deleted")


def workflows(telegram: bool) -> None:
    step("5/7 Workflows")
    files = IMPORT + (["03a_wf3_telegram"] if telegram else [])
    for f in files:
        run(["docker", "compose", "cp", f"workflows/{f}.json", f"n8n:/tmp/{f}.json"])
        n8n("import:workflow", f"--input=/tmp/{f}.json")
    print(f"✓ {len(files)} workflows imported")
    for wid in PUBLISH + ([TELEGRAM_ENTRY] if telegram else []):
        n8n("publish:workflow", f"--id={wid}")
    n8n("unpublish:workflow", f"--id={TEST_ENTRANCE}", check=False)   # test entrance: only during a run
    run(["docker", "compose", "restart", "n8n"])
    wait_for(f"{N8N_URL}/healthz", "n8n")
    time.sleep(8)   # webhooks register a few seconds after /healthz
    print(f"✓ {len(PUBLISH) + telegram} published; test entrance left unpublished")


def counts() -> dict:
    out = {}
    for c in COLLECTIONS:
        r = get_json(f"{QDRANT_URL}/collections/{c}")
        out[c] = r["result"]["points_count"] if r and r.get("result") else 0
    return out


def index() -> None:
    step("6/7 Regulations index (Qdrant)")
    if counts() == COLLECTIONS:
        print(f"✓ already indexed {COLLECTIONS}")
        return
    print("… running WF-1 (embeds 245 chunks with bge-m3 on CPU: ≈ 5–6 min)", flush=True)
    n8n("execute", f"--id={WF1}", env={"N8N_RUNNERS_BROKER_PORT": "5699"})   # own broker port: n8n's is taken
    got = counts()
    if got != COLLECTIONS:
        fail(f"index counts {got}, expected {COLLECTIONS} — see eval/retrieval/ingestion_log.md")
    print(f"✓ {got}")


def summary(telegram: bool, gemini: bool) -> None:
    step("7/7 Ready")
    mode = json.loads((ROOT / "config/agents.json").read_text(encoding="utf-8"))["mode"]
    print(f"n8n {N8N_URL} · Qdrant {QDRANT_URL}/dashboard · Ollama {OLLAMA_URL} · mode {mode}")
    if mode == "hybrid" and not gemini and not credential_exists(CREDS["gemini"]["id"]):
        print("! hybrid mode without a Gemini credential: regulation, draft and photo answers will fail.\n"
              "  Re-run with --gemini, or set \"mode\": \"local\" in config/agents.json, rebuild and re-run (slow on CPU).")
    print("Test it: .venv/Scripts/python -X utf8 scripts/workflows/smoke_wf3.py   (9 cases, opens and closes the test entrance)")
    if telegram:
        print("Telegram: open YOUR bot in Telegram, press Start, ask « C'est quand l'épreuve d'Advanced Deep Learning "
              "pour la classe 5DS6 ? »")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gemini", action="store_true", help="ask for your Gemini API key (hybrid mode)")
    ap.add_argument("--telegram", action="store_true", help="ngrok + your own Telegram bot")
    ap.add_argument("--replace-credentials", action="store_true", help="ask again even if the credential exists")
    ap.add_argument("--team-laptop", action="store_true", help=f"allow @{TEAM_BOT}'s token (the demo laptop only)")
    a = ap.parse_args()
    preflight(a.telegram)
    start(a.telegram)
    models()
    credentials(a.gemini, a.telegram, a.replace_credentials, a.team_laptop)
    workflows(a.telegram)
    index()
    summary(a.telegram, a.gemini)


if __name__ == "__main__":
    main()
