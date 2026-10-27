"""CF-400 / CF-421 — run a Regulations prompt version on exported contexts (Gemini Flash-Lite, the ADR-010 provider).

  --version v2|v3      template <!-- template:vN --> of prompts/P-REGULATIONS-001.md
  --set dev|t1         dev = D5 regulation questions (tune here) · t1 = final measurement, needs --final (run once)
  --via n8n|direct     see eval/agents/gemini_client.py (direct needs GEMINI_API_KEY in the environment)
Scores each reply with workflows/lib/checks.js (directory e-mails allowed): pass / failures; said « non trouvée »;
on T1 also: expected article cited, « not found » right on the 3 unanswerable rows. Writes:
  eval/agents/regulations_results/<set>_<version>.json   raw replies + scores (re-score with --score-only)
  eval/agents/regulations_results/review_<set>_<version>.md  one block per reply for the MANUAL check the code cannot
                                                         do: « does every sentence follow from the excerpts? » (T1-25)
  eval/agents/regulations_results/summary.md             all runs side by side
Run: python -X utf8 eval/agents/regulations_prompt_eval.py --version v3 --set dev --via direct [--limit N] [--score-only]
"""
import argparse
import csv
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/agents"))
import gemini_client as gc  # noqa: E402

OUT = ROOT / "eval/agents/regulations_results"
LIB = (ROOT / "prompts/P-REGULATIONS-001.md").read_text(encoding="utf-8")
EMAILS = [r["email"] for r in csv.DictReader(open(ROOT / "data/tables/directory.csv", encoding="utf-8"))]
CONTEXTS = {"dev": ROOT / "eval/agents/regulations_contexts_dev.jsonl", "t1": ROOT / "eval/agents/regulations_contexts_T1.jsonl"}


def template(version: str) -> str:
    m = re.search(r"<!-- template:" + version + r" -->\s*```text\n(.*?)\n```", LIB, re.S)
    if not m:
        raise SystemExit(f"template {version} not found in prompts/P-REGULATIONS-001.md")
    return m.group(1)


# From v4 on, the bot repairs the citation format in code before its checks (assistant.js normalizeCitations,
# CF-807): score exactly what the student sees. v1–v3 runs keep their original scoring.
REPAIRED = lambda version: version not in ("v1", "v2", "v3")  # noqa: E731


def checks(rows: list[dict], repair: bool = False) -> list[dict]:
    """Run checks.js once for all replies (node); with repair, on the reply as the bot shows it."""
    js = ("const {checkReply}=require('./workflows/lib/checks.js');const {normalizeCitations}=require('./workflows/lib/assistant.js');"
          "const x=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          "console.log(JSON.stringify(x.rows.map(r=>{const f=new Set(r.retrieved.filter(c=>c.doc_status==='FICTITIOUS')"
          ".flatMap(c=>c.article_keys.map(k=>k.split('/')[0])));const shown=x.repair?normalizeCitations(r.reply,f,/^(what|how|when|which|where|why|do|does|can|is|are)\b/i.test(r.q)?'en':'fr'):r.reply;"
          "return {shown,...checkReply(shown,{retrieved:r.retrieved,allowed:x.allowed})};})));")
    payload = {"rows": [{"reply": r["reply"], "retrieved": r["retrieved"], "q": r["question"]} for r in rows], "allowed": EMAILS, "repair": repair}
    return json.loads(subprocess.run(["node", "-e", js], cwd=ROOT, input=json.dumps(payload), capture_output=True,
                                     text=True, encoding="utf-8", check=True).stdout)


def score(rows: list[dict], repair: bool = False) -> dict:
    for r, c in zip(rows, checks(rows, repair)):
        r["checks_pass"], r["check_failures"] = c["pass"], [f["check"] for f in c["failures"]]
        if repair:
            r["shown"] = c["shown"]
        r["said_not_found"] = "non trouvée" in r["reply"].lower() or "not found" in r["reply"].lower()
        exp = [k for k in r["expected_article"].split("|") if k]
        cited = {f"{d}/{a}" for d, a in re.findall(r"\[(D1-\d{3}), art\. ([\w-]+)", r["reply"])}
        r["expected_cited"] = any("/".join(k.split("/")[:2]) in cited for k in exp) if exp else None
    t1 = [r for r in rows if r["answerable"]]
    s = {"n": len(rows), "checks_pass": sum(r["checks_pass"] for r in rows),
         "failures": {f: sum(f in r["check_failures"] for r in rows) for f in sorted({f for r in rows for f in r["check_failures"]})},
         "said_not_found": sum(r["said_not_found"] for r in rows), "seconds_mean": round(statistics.mean(r["seconds"] for r in rows), 2),
         "tokens_max": max(r.get("output_tokens") or 0 for r in rows), "over_160_tokens": sum((r.get("output_tokens") or 0) > 160 for r in rows)}
    if t1:
        ans = [r for r in t1 if r["answerable"] == "yes"]
        una = [r for r in t1 if r["answerable"] == "no"]
        s["expected_cited"] = f"{sum(bool(r['expected_cited']) for r in ans)}/{len(ans)}"
        s["not_found_right"] = f"{sum(r['said_not_found'] for r in una)}/{len(una)}"
        s["not_found_wrong"] = sum(r["said_not_found"] for r in ans)
    return s


def review_sheet(rows: list[dict], name: str) -> None:
    L = [f"# Manual review — Regulations {name}", "",
         "For each reply: does **every sentence** follow from the excerpts? Tick `[x] grounded` or write the invented part.",
         "For each « non trouvée »: do the excerpts actually answer it (possibly per regime)? A « non trouvée » always passes",
         "the automatic checks, so this box is the only way to see an over-cautious prompt.",
         "The automatic checks (citations, numbers, dates, contacts, FICTIF label) are already in the header line.", ""]
    for r in rows:
        L += [f"## {r['id']} ({r['regime']}) — checks: {'PASS' if r['checks_pass'] else ', '.join(r['check_failures'])}", "",
              f"**Question:** {r['question']}", "", "**Reply:**", "", "> " + r.get("shown", r["reply"]).replace("\n", "\n> "), "",
              "**Excerpts used:** " + " · ".join(k for c in r["retrieved"] for k in c["article_keys"]), "",
              "- [ ] grounded  [ ] invented: ____  [ ] « non trouvée » à tort (the excerpts answer it): ____", ""]
    (OUT / f"review_{name}.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def summary() -> None:
    L = ["# Regulations prompt runs (Gemini Flash-Lite)", "", "Generated by `regulations_prompt_eval.py` from the saved runs.", "",
         "| Run | Questions | Checks pass | Failures | Said « non trouvée » | Expected cited (T1) | Not found right (T1) | Mean s |",
         "|---|---:|---:|---|---:|---:|---:|---:|"]
    for p in sorted(OUT.glob("*_v*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))["summary"]
        fails = ", ".join(f"{k} {v}" for k, v in s["failures"].items()) or "—"
        L.append(f"| {p.stem} | {s['n']} | {s['checks_pass']} | {fails} | {s['said_not_found']} | {s.get('expected_cited', '—')} | "
                 f"{s.get('not_found_right', '—')} | {s['seconds_mean']} |")
    (OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--set", choices=["dev", "t1"], default="dev")
    ap.add_argument("--via", choices=["n8n", "direct"], default="n8n")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--final", action="store_true", help="required for --set t1: T1 is measured once, not tuned on")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--pause", type=float, default=4.0, help="seconds between calls (free-tier rate limit)")
    a = ap.parse_args()
    if a.set == "t1" and not a.final:
        raise SystemExit("T1 is the final test set: tune on --set dev; run T1 once with --final")
    OUT.mkdir(parents=True, exist_ok=True)
    name = f"{a.set}_{a.version}"
    path = OUT / f"{name}.json"
    if a.score_only:
        rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    else:
        system = template(a.version)
        ctx = [json.loads(x) for x in CONTEXTS[a.set].read_text(encoding="utf-8").splitlines() if x.strip()][: a.limit]
        rows = []
        for c in ctx:
            out = gc.generate(system, c["user"], max_tokens=200, temperature=0.1, via=a.via)
            rows.append({**{k: c[k] for k in ("id", "regime", "answerable", "question", "expected_article", "retrieved")},
                         "reply": out["text"].strip(), "seconds": out["seconds"], "output_tokens": out["output_tokens"]})
            print(f"{c['id']} {out['seconds']} s", flush=True)
            time.sleep(a.pause)
    s = score(rows, REPAIRED(a.version))
    path.write_text(json.dumps({"version": a.version, "set": a.set, "via": a.via, "summary": s, "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    review_sheet(rows, name)
    summary()
    print(json.dumps(s, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
