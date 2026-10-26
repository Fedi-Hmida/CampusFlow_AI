"""CF-010 — option 2 of ADR-010: latency of the text agents on Gemini Flash-Lite instead of the local 4B model.

Same prompts as the local measurements: the Router v2 prompt (+ 11 examples) on 5 D5 dev questions, and the
Regulations v2 prompt on 3 T1 questions with their B / official-first context, rebuilt from Qdrant exactly as in
regulations_bench.py. Called through the temporary n8n workflow
00d_gemini_text_eval (key stays in the n8n credential). DATA LEAVING THE LAPTOP: the student question and public /
FICTITIOUS regulation excerpts — no personal data.
SECURITY: publish 00d only for the run, then unpublish and restart n8n (n8n is public through ngrok).
Raw: eval/latency/gemini_2026-10-26.jsonl · Run: .venv/Scripts/python -X utf8 eval/latency/gemini_bench.py
"""
import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/latency"))
import regulations_bench as rb  # noqa: E402  (same retrieval and prompt as the local measurement)

URL = "http://127.0.0.1:5678/webhook/gemini-text-eval"
RAW = ROOT / "eval/latency/gemini_2026-10-26.jsonl"
LIB = (ROOT / "prompts/P-ROUTER-001.md").read_text(encoding="utf-8")
ROUTER = re.search(r"<!-- template:v2 -->\s*```text\n(.*?)\n```", LIB, re.S).group(1)
SHOTS = json.loads((ROOT / "prompts/examples/router_examples_v2.json").read_text(encoding="utf-8"))["examples"]
ROUTER_SYS = ROUTER + "\n\nEXEMPLES (message → JSON) :\n" + "\n".join(
    json.dumps(e["message"], ensure_ascii=False) + " → " + json.dumps(e["output"], ensure_ascii=False) for e in SHOTS)


def gemini(system: str, user: str, max_tokens: int) -> dict:
    t0 = time.time()
    req = urllib.request.Request(URL, data=json.dumps({"system": system, "user": user, "max_tokens": max_tokens}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        o = json.loads(r.read().decode())
    o = o[0] if isinstance(o, list) else o
    u = o.get("usageMetadata", {})
    return {"wall_s": round(time.time() - t0, 2), "prompt_tokens": u.get("promptTokenCount"), "output_tokens": u.get("candidatesTokenCount"),
            "text": o["candidates"][0]["content"]["parts"][0]["text"]}


def main() -> None:
    out = []
    dev = [r for r in csv.DictReader(open(ROOT / "eval/candidates/D5_triage.csv", encoding="utf-8")) if r["router_dev"] == "yes"]
    for r in dev[:: max(1, len(dev) // 5)][:5]:
        rec = {"agent": "router", "id": r["d5_id"], **gemini(ROUTER_SYS, json.dumps({"message": r["question"]}, ensure_ascii=False), 120)}
        out.append(rec); print({k: v for k, v in rec.items() if k != "text"}, flush=True)
        time.sleep(4)
    t1 = {r["id"]: r for r in csv.DictReader(open(ROOT / "eval/testsets/T1_regulations.csv", encoding="utf-8"))}
    vecs = dict(zip(t1, json.loads((ROOT / "eval/retrieval/question_vectors_T1.json").read_text(encoding="utf-8"))))
    for i in ("T1-01", "T1-13", "T1-23"):
        r = t1[i]
        chunks = rb.retrieve(vecs[i], r["regime"])
        context = "\n\n".join(f"{rb.ref(c)} ({'officiel' if c['doc_status'] == 'official' else 'FICTIF'})\n{c['text']}" for c in chunks)
        user = f"Régime de l'étudiant : {rb.REGIME_FR[r['regime']]}\nQuestion : {r['question']}\n\nEXTRAITS :\n{context}"
        rec = {"agent": "regulations", "id": i, **gemini(rb.SYSTEM, user, 200)}
        out.append(rec); print({k: v for k, v in rec.items() if k != "text"}, flush=True)
        time.sleep(4)
    RAW.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
