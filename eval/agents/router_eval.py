"""CF-022 — measure Router v1 (prompts/P-ROUTER-001.md) on the D5 Router development set, zero-shot vs few-shot.

Dev set: eval/candidates/D5_triage.csv rows with router_dev = yes (57; never T1–T5). Model: qwen3 4B (Ollama),
temperature 0, structured output with prompts/schemas/router.schema.json. Few-shot = the 30 examples of
prompts/examples/router_examples.md given as user / assistant turns (same system prompt, so Ollama reuses its prompt cache).
Metrics: valid JSON, schema-valid, intents exact match and Jaccard, language, regime invented (none in the question but
filled), regime missed (stated but null), out-of-scope precision / recall, seconds per call.
Raw outputs: eval/agents/router_results/<variant>.json (re-score with --score-only). Summary: router_results/summary.json
Run: .venv/Scripts/python -X utf8 eval/agents/router_eval.py [--variants zero few] [--limit N] [--score-only]
"""
import argparse
import csv
import json
import re
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/agents"))
from vision_prompt_eval import schema_errors  # noqa: E402  (same JSON-Schema subset checker)

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"
OUT = ROOT / "eval/agents/router_results"
SCHEMA = json.loads((ROOT / "prompts/schemas/router.schema.json").read_text(encoding="utf-8"))
SYSTEM = re.search(r"<!-- template:v1 -->\s*```text\n(.*?)\n```", (ROOT / "prompts/P-ROUTER-001.md").read_text(encoding="utf-8"), re.S).group(1)
ENT = ["module_code", "module_name", "class_group", "session", "assessment", "regime", "request_type", "topic"]


def examples() -> list[dict]:
    """The 30 Router examples as chat turns: user message → assistant JSON in the schema."""
    turns = []
    for ln in (ROOT / "prompts/examples/router_examples.md").read_text(encoding="utf-8").splitlines():
        if not re.match(r"\| R\d\d ", ln):
            continue
        _, _, msg, intents, lang, agents, ents, _ = [c.strip() for c in ln.split("|")]
        e, missing = {k: None for k in ENT}, []
        for kv in [x.strip() for x in ents.split(";") if "=" in x]:
            k, v = kv.split("=", 1)
            if v == "missing":
                missing.append({"module_code": "module", "class_group": "class_group", "regime": "regime", "session": "session"}.get(k, k))
            elif k in e:
                e[k] = v
        photo = msg.startswith("[Photo")
        out = {"language": lang, "intents": [i.strip() for i in intents.split(";")],
               "agents": [] if agents == "none" else [a.strip() for a in agents.split(",")],
               "entities": e, "has_photo": photo, "missing_fields": missing,
               "injection_suspected": "injection_suspected=true" in ents}
        turns += [{"role": "user", "content": json.dumps({"message": msg, "has_photo": photo}, ensure_ascii=False)},
                  {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}]
    return turns


def call(messages: list[dict]) -> tuple[str, float]:
    body = {"model": MODEL, "messages": messages, "stream": False, "format": SCHEMA,
            "options": {"temperature": 0, "num_predict": 200}, "keep_alive": "30m"}
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read().decode())
    return out["message"]["content"], time.time() - t0


def score(row: dict, raw: str) -> dict:
    res = {"id": row["d5_id"], "valid_json": False}
    try:
        o = json.loads(raw)
    except json.JSONDecodeError:
        return res
    res["valid_json"] = True
    res["schema_errors"] = schema_errors(o, SCHEMA)
    want = set(row["router_intents"].split(";")) - {"vision"}       # vision is an agent, not an intent (schema)
    got = set(o.get("intents") or [])
    res["intents_exact"] = got == want
    res["intents_jaccard"] = len(got & want) / len(got | want) if got | want else 1.0
    res["language_ok"] = o.get("language") == row["language"]
    reg = (o.get("entities") or {}).get("regime")
    res["regime_invented"] = bool(reg) and not row["regime_in_question"]
    res["regime_missed"] = bool(row["regime_in_question"]) and not reg
    res["oos_expected"], res["oos_predicted"] = "out_of_scope" in want, "out_of_scope" in got
    res["predicted"], res["expected"] = sorted(got), sorted(want)
    return res


def summarise(scores: list[dict], secs: list[float]) -> dict:
    v = [s for s in scores if s["valid_json"]]
    tp = sum(s["oos_expected"] and s["oos_predicted"] for s in v)
    return {"rows": len(scores), "valid_json": len(v), "schema_valid": sum(not s["schema_errors"] for s in v),
            "intents_exact": sum(s["intents_exact"] for s in v), "intents_jaccard_mean": round(statistics.mean(s["intents_jaccard"] for s in v), 3),
            "language_ok": sum(s["language_ok"] for s in v), "regime_invented": sum(s["regime_invented"] for s in v),
            "regime_missed": sum(s["regime_missed"] for s in v),
            "oos_precision": round(tp / max(1, sum(s["oos_predicted"] for s in v)), 3),
            "oos_recall": round(tp / max(1, sum(s["oos_expected"] for s in v)), 3),
            "seconds_mean": round(statistics.mean(secs), 1) if secs else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["zero", "few"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(ROOT / "eval/candidates/D5_triage.csv", encoding="utf-8")) if r["router_dev"] == "yes"][: a.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    shots = examples()
    summary = {}
    for v in a.variants:
        path = OUT / f"{v}.json"
        if not a.score_only:
            raws = {}
            for r in rows:
                msg = {"role": "user", "content": json.dumps({"message": r["question"], "has_photo": r["has_photo"] == "yes"}, ensure_ascii=False)}
                raw, secs = call([{"role": "system", "content": SYSTEM}] + (shots if v == "few" else []) + [msg])
                raws[r["d5_id"]] = {"raw": raw, "seconds": round(secs, 1)}
                print(f"{v} {r['d5_id']} {secs:.1f}s", flush=True)
            path.write_text(json.dumps(raws, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        raws = json.loads(path.read_text(encoding="utf-8"))
        scores = [score(r, raws[r["d5_id"]]["raw"]) for r in rows if r["d5_id"] in raws]
        (OUT / f"scores_{v}.json").write_text(json.dumps(scores, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        summary[v] = summarise(scores, [raws[r["d5_id"]]["seconds"] for r in rows if r["d5_id"] in raws])
    if not a.limit:
        (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
