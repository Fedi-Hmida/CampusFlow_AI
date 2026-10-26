"""CF-010 — Ollama tuning on the reference laptop (i5-1135G7, 4 cores / 8 threads, CPU only).

Two questions for the latency decision (ADR-010):
  1. threads  does num_thread 8 (hyper-threads) beat the default 4 physical cores for prefill and generation?
  2. cache    when consecutive calls share the same static prefix (system prompt + few-shot examples), does Ollama
              skip re-reading it? (prompt_eval_count of calls 2..n vs call 1)
Timings come from Ollama's own counters (prompt_eval_* / eval_*), not wall clock. Each thread setting gets one warm-up
call (a new num_thread reloads the model) that is not counted.
Raw: eval/latency/tuning_2026-10-26.jsonl · Run: .venv/Scripts/python -X utf8 eval/latency/tuning_bench.py [--alternate | --retrieval]
"""
import json
import re
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"
RAW = ROOT / "eval/latency/tuning_2026-10-26.jsonl"
CHUNKS = json.loads((ROOT / "data/index/chunks_B.json").read_text(encoding="utf-8"))
CONTEXT = "\n\n".join(c["text"] for c in CHUNKS if c["doc_id"] == "D1-001")[:4000]   # ≈ 1 000 tokens of real regulation text
STATIC = ("Tu es l'agent Règlements de CampusFlow AI. Réponds uniquement à partir des extraits, cite [document, article, "
          "page], sinon dis « information non trouvée ».\n\nEXTRAITS :\n" + CONTEXT)


def chat(system: str, user: str, num_predict: int, num_thread: int | None = None) -> dict:
    opts = {"temperature": 0, "num_predict": num_predict}
    if num_thread:
        opts["num_thread"] = num_thread
    body = {"model": MODEL, "stream": False, "keep_alive": "30m", "options": opts,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        o = json.loads(r.read().decode())
    ns = 1e9
    return {"prompt_tokens": o.get("prompt_eval_count", 0), "prompt_s": round(o.get("prompt_eval_duration", 0) / ns, 1),
            "output_tokens": o.get("eval_count", 0), "output_s": round(o.get("eval_duration", 0) / ns, 1),
            "load_s": round(o.get("load_duration", 0) / ns, 1), "wall_s": round(time.time() - t0, 1)}


def rates(r: dict) -> dict:
    r["prompt_tps"] = round(r["prompt_tokens"] / r["prompt_s"], 1) if r["prompt_s"] else None
    r["output_tps"] = round(r["output_tokens"] / r["output_s"], 2) if r["output_s"] else None
    return r


def alternate() -> None:
    """3. alternate  WF-3 alternates agents (Router, Regulations, Router…): is the Router's cached prefix still there
    after a Regulations call in between? (Ollama default: one parallel slot.)"""
    router_sys = re.search(r"<!-- template:v2 -->\s*```text\n(.*?)\n```", (ROOT / "prompts/P-ROUTER-001.md").read_text(encoding="utf-8"), re.S).group(1)
    shots = json.dumps(json.loads((ROOT / "prompts/examples/router_examples_v2.json").read_text(encoding="utf-8"))["examples"], ensure_ascii=False)
    router_prefix = router_sys + "\n\nEXEMPLES :\n" + shots
    rows = []
    plan = [("router", router_prefix, "Quand est mon examen de DS14 ? Je suis en 5DS6."),
            ("router", router_prefix, "Qui délivre les attestations de scolarité ?"),
            ("regulations", STATIC, "Quelles sont les règles d'assiduité ?"),
            ("router", router_prefix, "Combien de fois peut-on redoubler ?")]
    for step, (agent, system, q) in enumerate(plan, 1):
        r = rates(chat(system, q, 16, 4))
        rows.append({"test": "alternate", "step": step, "agent": agent, **r})
        print(rows[-1], flush=True)
    with open(RAW, "a", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")


def retrieval() -> None:
    """4. retrieval  wall time of one question: bge-m3 embedding + the two official-first Qdrant queries (ADR-025)."""
    questions = ["Je suis absent à un examen pour maladie, que faire ?", "Combien de crédits pour passer en année supérieure ?",
                 "Quel est le délai pour une réclamation de note ?", "Qui contacter pour un stage ?", "Peut-on redoubler deux fois ?"]
    rows = []
    for q in questions:
        t0 = time.time()
        req = urllib.request.Request("http://127.0.0.1:11434/api/embed", data=json.dumps({"model": "bge-m3:567m", "input": [q]}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            vec = json.loads(r.read().decode())["embeddings"][0]
        embed_s = time.time() - t0
        for status, n in (("official", 3), ("FICTITIOUS", 2)):
            body = {"query": vec, "limit": n, "with_payload": True,
                    "filter": {"must": [{"key": "doc_status", "match": {"value": status}}, {"key": "regimes", "match": {"any": ["jour"]}}]}}
            req = urllib.request.Request("http://127.0.0.1:6333/collections/regs_structured/points/query", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=60).read()
        rows.append({"test": "retrieval", "embed_s": round(embed_s, 2), "wall_s": round(time.time() - t0, 2)})
        print(rows[-1], flush=True)
    with open(RAW, "a", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")


def main() -> None:
    if "--alternate" in sys.argv:
        return alternate()
    if "--retrieval" in sys.argv:
        return retrieval()
    rows = []
    for threads in (4, 8):
        chat("échauffement", "Bonjour", 4, threads)                                  # reload with this setting
        for run in (1, 2):
            nonce = uuid.uuid4().hex                                                # unique start: no cache reuse
            r = rates(chat(f"[{nonce}] " + STATIC, "Quelles sont les règles d'assiduité ?", 64, threads))
            rows.append({"test": "threads", "num_thread": threads, "run": run, **r})
            print(rows[-1], flush=True)
    questions = ["Quelles sont les règles d'assiduité ?", "Comment se calcule la moyenne d'un module ?",
                 "Que se passe-t-il en cas d'absence à un examen ?"]
    for i, q in enumerate(questions, 1):                                            # same static prefix each time
        r = rates(chat(STATIC, q, 32, 4))
        rows.append({"test": "cache", "call": i, **r})
        print(rows[-1], flush=True)
    RAW.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
