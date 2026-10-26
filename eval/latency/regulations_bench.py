"""CF-010 — measure the Regulations call as WF-3 will run it (ADR-010): real context, real prompt, real checks.

For 10 T1 questions (3 regimes, 2 former retrieval failures, 2 FICTITIOUS-sourced, 2 unanswerable):
  retrieval  Qdrant regs_structured (B), regime filter, official-first quota 3 + 2 (ADR-025)
  call       P-REGULATIONS-001 v2 (text reply), qwen3 4B, temperature 0.1, num_predict 160
  checks     workflows/lib/checks.js on the reply (deterministic Critic) — run with node
Records Ollama's counters (prompt / output tokens and seconds) and the reply.
Raw: eval/latency/regulations_2026-10-26.jsonl · Run: .venv/Scripts/python -X utf8 eval/latency/regulations_bench.py [--rescore]
This is a latency measurement, not the T1 evaluation of the bot (that is WF-3, Phase 4); replies are kept as a preview.
"""
import csv
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLLAMA, QDRANT = "http://127.0.0.1:11434", "http://127.0.0.1:6333"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"
IDS = ["T1-01", "T1-02", "T1-07", "T1-09", "T1-11", "T1-13", "T1-17", "T1-20", "T1-23", "T1-25"]
RAW = ROOT / "eval/latency/regulations_2026-10-26.jsonl"
SYSTEM = re.search(r"<!-- template:v2 -->\s*```text\n(.*?)\n```", (ROOT / "prompts/P-REGULATIONS-001.md").read_text(encoding="utf-8"), re.S).group(1)
REGIME_FR = {"jour": "cours du jour", "soir": "cours du soir", "alternance": "alternance", "all": "non précisé (règle commune)"}


def post(url: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read().decode())


def retrieve(vector: list[float], regime: str) -> list[dict]:
    out = []
    for status, n in (("official", 3), ("FICTITIOUS", 2)):
        must = [{"key": "doc_status", "match": {"value": status}}]
        if regime != "all":
            must.append({"key": "regimes", "match": {"any": regime.split(";")}})
        res = post(f"{QDRANT}/collections/regs_structured/points/query",
                   {"query": vector, "limit": n, "with_payload": True, "filter": {"must": must}})["result"]["points"]
        out += [{**p["payload"], "score": p["score"]} for p in res]
    return sorted(out, key=lambda c: -c["score"])


def ref(c: dict) -> str:
    num = c["article_keys"][-1].split("/")[1]
    return f"[{c['doc_id']}, art. {num}, p. {c['page_start']}]"


DIRECTORY_EMAILS = [r["email"] for r in csv.DictReader(open(ROOT / "data/tables/directory.csv", encoding="utf-8"))]
# Manual review of the replies (things the deterministic checks cannot see)
MANUAL = {"T1-25": "invented rule: « ne peut pas être effectué à l'étranger » — D1-001/7-9 never mentions abroad"}


def run_checks(reply: str, chunks: list[dict]) -> dict:
    """workflows/lib/checks.js through node; directory e-mails are allowed facts (the prompt names scolarite@…)."""
    evidence = [{"article_keys": c["article_keys"], "doc_status": c["doc_status"], "text": c["text"]} for c in chunks]
    return json.loads(subprocess.run(["node", "-e", "const {checkReply}=require('./workflows/lib/checks.js');"
                                      "const x=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                                      "console.log(JSON.stringify(checkReply(x.reply,{retrieved:x.retrieved,allowed:x.allowed})));"],
                                     cwd=ROOT, input=json.dumps({"reply": reply, "retrieved": evidence, "allowed": DIRECTORY_EMAILS}),
                                     capture_output=True, text=True, encoding="utf-8", check=True).stdout)


def rescore() -> None:
    """Re-run the checks on the saved local and Gemini replies (no model call); retrieval is deterministic."""
    rows = {r["id"]: r for r in csv.DictReader(open(ROOT / "eval/testsets/T1_regulations.csv", encoding="utf-8"))}
    vecs = dict(zip(rows, json.loads((ROOT / "eval/retrieval/question_vectors_T1.json").read_text(encoding="utf-8"))))
    for path, field in ((RAW, "reply"), (ROOT / "eval/latency/gemini_2026-10-26.jsonl", "text")):
        recs = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        for rec in recs:
            if rec.get("agent", "regulations") != "regulations":
                continue
            chk = run_checks(rec[field], retrieve(vecs[rec["id"]], rows[rec["id"]]["regime"]))
            rec["checks_pass"], rec["check_failures"] = chk["pass"], [f["check"] for f in chk["failures"]]
            rec["manual_review"] = MANUAL.get(rec["id"], "") if path == RAW else rec.get("manual_review", "")
            print(path.name, rec["id"], "PASS" if chk["pass"] else rec["check_failures"], rec["manual_review"])
        path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in recs) + "\n", encoding="utf-8")


def main() -> None:
    if "--rescore" in sys.argv:
        return rescore()
    rows = {r["id"]: r for r in csv.DictReader(open(ROOT / "eval/testsets/T1_regulations.csv", encoding="utf-8"))}
    ids_all = [r for r in rows]
    vec_cache = ROOT / "eval/retrieval/question_vectors_T1.json"
    vecs = dict(zip(ids_all, json.loads(vec_cache.read_text(encoding="utf-8")))) if vec_cache.exists() else {}
    out = []
    for i in IDS:
        r = rows[i]
        v = vecs.get(i) or post(f"{OLLAMA}/api/embed", {"model": "bge-m3:567m", "input": [r["question"]]})["embeddings"][0]
        chunks = retrieve(v, r["regime"])
        context = "\n\n".join(f"{ref(c)} ({'officiel' if c['doc_status'] == 'official' else 'FICTIF'})\n{c['text']}" for c in chunks)
        user = f"Régime de l'étudiant : {REGIME_FR[r['regime']]}\nQuestion : {r['question']}\n\nEXTRAITS :\n{context}"
        t0 = time.time()
        o = post(f"{OLLAMA}/api/chat", {"model": MODEL, "stream": False, "keep_alive": "30m",
                                        "options": {"temperature": 0.1, "num_predict": 160},
                                        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]})
        wall = round(time.time() - t0, 1)
        reply = o["message"]["content"].strip()
        chk = run_checks(reply, chunks)
        expected = set(filter(None, r["expected_article"].split("|")))
        cited = {f"{d}/{a}" for d, a in re.findall(r"\[(D1-\d{3}), art\. ([\w-]+)", reply)}
        rec = {"id": i, "regime": r["regime"], "answerable": r["answerable"], "context_chars": len(context),
               "prompt_tokens": o.get("prompt_eval_count"), "prompt_s": round(o.get("prompt_eval_duration", 0) / 1e9, 1),
               "output_tokens": o.get("eval_count"), "output_s": round(o.get("eval_duration", 0) / 1e9, 1), "wall_s": wall,
               "expected_cited": any(k.split("/")[0] + "/" + k.split("/")[1] in cited for k in expected) if expected else None,
               "said_not_found": "non trouvée" in reply.lower(), "checks_pass": chk["pass"],
               "check_failures": [f["check"] for f in chk["failures"]], "reply": reply}
        out.append(rec)
        print({k: v for k, v in rec.items() if k != "reply"}, flush=True)
    RAW.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
