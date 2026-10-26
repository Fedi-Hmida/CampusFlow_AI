"""CF-019 — live test of the n8n lookup tools: the deployed workflow must return exactly what lookup.js returns locally.

Sends each query through the temporary webhook workflow 03t_tools_test (Webhook → Execute Workflow by id) and compares
the JSON with `node` running workflows/lib/lookup.js on the same CSV files. 15 queries (5 per tool).
SECURITY: n8n is public through ngrok — publish 03t_tools_test only for this run, then unpublish and restart n8n.
Run: .venv/Scripts/python -X utf8 eval/agents/tools_live_test.py   → writes eval/agents/tools_test.md
"""
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "http://localhost:5678/webhook/tools-test"
TOOLS = {"exam": ("cfToolExam000001", "lookupExam(CAL, q)"), "contact": ("cfToolContact001", "lookupContact(DIR, q)"),
         "request": ("cfToolRequest001", "lookupRequest(REQ, DIR, q)")}
CASES = [
    ("exam", {"module": "Advanced Deep Learning", "class_group": "5DS6", "session": "Principale"}),
    ("exam", {"module": "ds14", "class_group": "5ds6", "session": "session de contrôle"}),
    ("exam", {"module": "Financial Analysis", "class_group": "3A1", "session": "Rattrapage"}),
    ("exam", {"module": "Quantum Computing", "class_group": "5DS6"}),
    ("exam", {"module": "DS14"}),
    ("contact", {"role_id": "FIN"}),
    ("contact", {"class_group": "3A12"}),
    ("contact", {"topic": "mobilité internationale"}),
    ("contact", {"role_id": "XYZ"}),
    ("contact", {}),
    ("request", {"request_id": "REQ-01", "class_group": "4SE1"}),
    ("request", {"request_id": "REQ-08"}),
    ("request", {"request_id": "REQ-08", "regime": "soir"}),
    ("request", {"topic": "convention de stage", "regime": "jour"}),
    ("request", {"request_id": "REQ-14", "regime": "soir"}),
]
NODE = """
const L = require('./workflows/lib/lookup.js'); const fs = require('fs');
const csv = f => L.parseCsv(fs.readFileSync('data/tables/' + f, 'utf8'));
const CAL = csv('exam_calendar.csv'), DIR = csv('directory.csv'), REQ = csv('request_catalogue.csv');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const { lookupExam, lookupContact, lookupRequest } = L;
console.log(JSON.stringify(cases.map(([expr, q]) => eval(expr))));
"""


def live(workflow_id: str, query: dict) -> dict:
    body = json.dumps({"workflow_id": workflow_id, "query": query}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    return out[0] if isinstance(out, list) else out


def main() -> None:
    local = json.loads(subprocess.run(["node", "-e", NODE], cwd=ROOT, input=json.dumps([[TOOLS[t][1], q] for t, q in CASES]),
                                      capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    lines = ["# Lookup tools — live test (CF-019)", "",
             "Each query is sent to the deployed n8n tool workflow (through the temporary webhook `03t_tools_test`) and to",
             "`workflows/lib/lookup.js` run locally with Node on the same CSV files. **Pass = identical JSON.**",
             "Unit tests of the same code: `node --test workflows/lib/lookup.test.js` (30 tests).", "",
             "| # | Tool | Query | Status | Result | Live = local |", "|---|---|---|---|---|---|"]
    ok = 0
    for i, ((tool, q), loc) in enumerate(zip(CASES, local), 1):
        got = live(TOOLS[tool][0], q)
        same = got == loc
        ok += same
        res = (got.get("matches", [{}])[0].get("exam_id") if tool == "exam" and got.get("found") else
               (got.get("contact") or {}).get("role_id") if tool == "contact" and got.get("found") else
               f"{(got.get('request') or {}).get('request_id')} → {got.get('handler_role_id')}" if tool == "request" and got.get("found") else
               ", ".join(got.get("needs", []) or got.get("candidates", [])) or "—")
        lines.append(f"| {i} | {tool} | `{json.dumps(q, ensure_ascii=False)}` | {got.get('status')} | {res} | {'✅' if same else '❌'} |")
    lines += ["", f"**{ok}/{len(CASES)} identical.**"]
    (ROOT / "eval/agents/tools_test.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-len(CASES) - 2:]))


if __name__ == "__main__":
    main()
