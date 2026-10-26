"""CF-400 — export the Regulations inputs of a question set, so prompts can be tested without Docker / Qdrant.

Two sets — tune on dev, measure T1 once (evaluation hygiene):
  --set dev  the D5 Router-dev questions routed to regulations (synthetic, answers unverified → scored by the
             deterministic checks + manual review only)  → eval/agents/regulations_contexts_dev.jsonl
  --set t1   the 25 verified T1 questions (final measurement only)                → eval/agents/regulations_contexts_T1.jsonl
Each line = one question with the exact user message WF-3 will send to the Regulations agent: regime, question and the
5 excerpts of the accepted retrieval (strategy B, regime filter, 3 official + 2 FICTITIOUS — ADR-025), each with its
reference header [D1-xxx, art. N, p. P]. For T1 the expected article keys and the « answerable » flag are included for
scoring; dev rows carry no answer key and use regime « all » unless the question states one. The system prompt is NOT
exported: it comes from prompts/P-REGULATIONS-001.md (the version under test).
Run (Fedi's laptop, Qdrant up): .venv/Scripts/python -X utf8 eval/agents/export_regulations_contexts.py --set dev|t1
"""
import csv
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/latency"))
import regulations_bench as rb  # noqa: E402  (same retrieval, reference format and regime wording as the measurements)

OUT = {"t1": ROOT / "eval/agents/regulations_contexts_T1.jsonl", "dev": ROOT / "eval/agents/regulations_contexts_dev.jsonl"}


def embed(texts: list[str]) -> list[list[float]]:
    req = urllib.request.Request("http://127.0.0.1:11434/api/embed", data=json.dumps({"model": "bge-m3:567m", "input": texts}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())["embeddings"]


def load(which: str) -> list[dict]:
    if which == "t1":
        return list(csv.DictReader(open(ROOT / "eval/testsets/T1_regulations.csv", encoding="utf-8")))
    d5 = csv.DictReader(open(ROOT / "eval/candidates/D5_triage.csv", encoding="utf-8"))
    return [{"id": r["d5_id"], "regime": r["regime_in_question"] or "all", "answerable": "", "question": r["question"],
             "expected_article": "", "expected_answer": ""}
            for r in d5 if r["router_dev"] == "yes" and "regulations" in r["router_intents"].split(";")]


def main() -> None:
    which = sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else "dev"
    rows = load(which)
    vecs = embed([r["question"] for r in rows])
    out = []
    for r, v in zip(rows, vecs):
        chunks = rb.retrieve(v, r["regime"])
        context = "\n\n".join(f"{rb.ref(c)} ({'officiel' if c['doc_status'] == 'official' else 'FICTIF'})\n{c['text']}" for c in chunks)
        out.append({"id": r["id"], "regime": r["regime"], "answerable": r["answerable"], "question": r["question"],
                    "expected_article": r["expected_article"], "expected_answer": r["expected_answer"],
                    "retrieved": [{"article_keys": c["article_keys"], "doc_status": c["doc_status"], "text": c["text"]} for c in chunks],
                    "user": f"Régime de l'étudiant : {rb.REGIME_FR[r['regime']]}\nQuestion : {r['question']}\n\nEXTRAITS :\n{context}"})
    OUT[which].write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n", encoding="utf-8")
    print(f"{OUT[which].relative_to(ROOT).as_posix()}: {len(out)} questions")


if __name__ == "__main__":
    main()
