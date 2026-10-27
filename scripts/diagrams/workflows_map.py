"""One-image overview of the n8n workflows, drawn from workflows/*.json (node positions and links as in n8n).

Run: .venv/Scripts/python scripts/diagrams/workflows_map.py
Out: diagrams/workflows_map.html and diagrams/workflows_map.png (PNG needs Edge or Chrome, plus Pillow to trim).
"""
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
OUT = ROOT / "diagrams"
S = 0.55            # n8n canvas units → pixels
BOX = 50            # node square
PAD = 34            # panel inner margin

COLORS = {"trigger": "#2e9e5b", "code": "#e8833a", "if": "#7b5cd6", "call": "#13998f", "http": "#3b7dd8",
          "file": "#7d8794", "telegram": "#2aa1d8", "respond": "#2e9e5b"}

# (file, status, role); order = order on the image
PANELS = [
    ("03a_wf3_telegram", "pub", "Telegram entrance: owns the bot, acknowledges, calls the assistant, replies, logs the run"),
    ("03b_wf3_test", "test", "Test entrance (POST /webhook/wf3-test) for the evaluation harness: published only during tests"),
    ("03_wf3_assistant", "pub", "The assistant (orchestrator): Router → Vision / Regulations / Calendar / Admin → merged reply"),
    ("20_llm_call", "pub", "Every model call: Gemini Flash-Lite or local Ollama, chosen by config/agents.json"),
    ("10_tool_lookup_exam", "pub", "Tool: exact exam lookup in exam_calendar.csv"),
    ("11_tool_lookup_contact", "pub", "Tool: office and e-mail from directory.csv"),
    ("12_tool_lookup_request", "pub", "Tool: administrative procedure from request_catalogue.csv"),
    ("04_wf4_errors", "pub", "Error workflow: any crash → logs/errors.jsonl (no question text, no chat id)"),
    ("01_wf1_index_regs", "manual", "Indexing (run once): chunks → bge-m3 embeddings → Qdrant regs_structured + regs_fixed"),
    ("02_wf2_tables_check", "manual", "Table check (run once): reads the CSV tables and reports row counts"),
]
# the assistant is 9 000 units wide: wrap it into three lines at its natural stages
WRAP = {"03_wf3_assistant": [(0, 2900, "1 · Input, greetings / commands, photo, Router, out-of-scope, Vision"),
                             (3000, 5800, "2 · Regulations agent (RAG over Qdrant + checks + one revision)"),
                             (5900, 9100, "3 · Calendar and Admin agents (exact tools) → Output")]}
STATUS = {"pub": ("Published", "#2e9e5b"), "test": ("Test only · off", "#c98a12"), "manual": ("Manual run", "#7d8794")}


def kind(t):
    t = t.split(".")[-1]
    if t.endswith("Trigger") or t in ("webhook",):
        return "trigger"
    return {"code": "code", "if": "if", "executeWorkflow": "call", "httpRequest": "http", "telegram": "telegram",
            "respondToWebhook": "respond"}.get(t, "file")


def tag(n, k):
    t = n["type"].split(".")[-1]
    if k == "trigger":
        return {"telegramTrigger": "TG", "webhook": "POST", "errorTrigger": "ERR", "manualTrigger": "▶"}.get(t, "⚡")
    return {"code": "JS", "if": "IF", "call": "↗", "http": "HTTP", "telegram": "TG", "respond": "200",
            "file": "FILE"}[k]


def sub(n, k, names):
    p = n["parameters"]
    if k == "call":
        return "→ " + names.get((p.get("workflowId") or {}).get("value"), "?")
    if k == "http":
        u = p.get("url", "")
        return "Gemini" if "generativelanguage" in u else "Ollama" if "ollama" in u else "Qdrant" if "qdrant" in u else ""
    return ""


def wrap(text, width=17):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]


def edge_label(src_kind, i, src_node):
    if src_kind == "if":
        return "true" if i == 0 else "false"
    if i == 1 and src_node.get("onError") == "continueErrorOutput":
        return "error"
    return ""


def panel_svg(w, names):
    nodes = {n["name"]: n for n in w["nodes"]}
    rows = WRAP.get(w["name"], [(-1, 10 ** 6, None)])
    ys = [n["position"][1] for n in w["nodes"]]
    y0, y1 = min(ys), max(ys)
    title_h = 22 if rows[0][2] else 0
    row_h = (y1 - y0) * S + BOX + 62 + title_h
    pos = {}
    for name, n in nodes.items():
        x, y = n["position"]
        r = next(i for i, (a, b, _) in enumerate(rows) if a <= x < b)
        x0 = rows[r][0] if rows[r][0] >= 0 else 0
        pos[name] = (PAD + (x - x0) * S + BOX / 2, PAD + r * row_h + title_h + (y - y0) * S + BOX / 2, r)
    right = max(p[0] for p in pos.values()) + BOX / 2 + (50 if len(rows) > 1 else 14)
    width = right + (PAD if len(rows) > 1 else 0)
    height = len(rows) * row_h + PAD
    out = [f'<svg width="{width:.0f}" height="{height:.0f}" xmlns="http://www.w3.org/2000/svg">']
    for r, (_, _, title) in enumerate(rows):
        if title:
            out.append(f'<text x="{PAD - 6}" y="{PAD + r * row_h - 6}" class="rowt">{html.escape(title)}</text>')
        if r:
            out.append(f'<line x1="{PAD - 10}" x2="{width - 10}" y1="{PAD + r * row_h - 26}" y2="{PAD + r * row_h - 26}" class="sep"/>')
    gap_hits = {}
    for src, c in w["connections"].items():
        sk = kind(nodes[src]["type"])
        for i, outs in enumerate(c.get("main", [])):
            for o in outs:
                sx, sy, sr = pos[src]
                tx, ty, tr = pos[o["node"]]
                ax, bx = sx + BOX / 2, tx - BOX / 2
                if sr == tr:
                    d = max(30, (bx - ax) / 2)
                    path = f"M{ax},{sy} C{ax + d},{sy} {bx - d},{ty} {bx},{ty}"
                else:  # continue on the next line: right, down into the gap, back left, into the target
                    k = gap_hits.get(tr, 0)
                    gap_hits[tr] = k + 1
                    gy = PAD + tr * row_h - 14 - k * 7
                    rx_ = right - 6 - len(gap_hits) * 7 - k * 7   # down the right margin, never through a line
                    path = f"M{ax},{sy} H{rx_} V{gy} H{bx - 22} V{ty} H{bx}"
                out.append(f'<path d="{path}" class="edge"/>')
                out.append(f'<path d="M{bx - 7},{ty - 4} L{bx},{ty} L{bx - 7},{ty + 4}" class="arrow"/>')
                lab = edge_label(sk, i, nodes[src])
                if lab:
                    ly = sy + (-9 if ty < sy or (ty == sy and i == 0) else 14)
                    out.append(f'<text x="{ax + 6}" y="{ly}" class="elab {lab}">{lab}</text>')
    for name, n in nodes.items():
        x, y, _ = pos[name]
        k = kind(n["type"])
        col = COLORS[k]
        rx = "18" if k == "trigger" else "9"
        out.append(f'<rect x="{x - BOX / 2}" y="{y - BOX / 2}" width="{BOX}" height="{BOX}" rx="{rx}" '
                   f'fill="{col}1f" stroke="{col}" stroke-width="2"/>')
        out.append(f'<text x="{x}" y="{y + 5}" class="tag" fill="{col}">{html.escape(tag(n, k))}</text>')
        ly = y + BOX / 2 + 15
        for line in wrap(name):
            out.append(f'<text x="{x}" y="{ly}" class="lab">{html.escape(line)}</text>')
            ly += 14
        s = sub(n, k, names)
        if s:
            out.append(f'<text x="{x}" y="{ly}" class="sub" fill="{col}">{html.escape(s)}</text>')
    out.append("</svg>")
    return "\n".join(out), width


def system_map():
    """Hand-placed map of who calls whom."""
    boxes = {  # id: (x, y, w, label, sublabel, colour)
        "student": (10, 70, 130, "Student", "Telegram app", "#2aa1d8"),
        "harness": (10, 190, 130, "Eval harness", "Doua · T1–T5", "#c98a12"),
        "03a": (230, 70, 190, "03a_wf3_telegram", "entrance (bot)", "#2e9e5b"),
        "03b": (230, 190, 190, "03b_wf3_test", "entrance (tests)", "#c98a12"),
        "03": (490, 120, 210, "03_wf3_assistant", "orchestrator · 44 nodes", "#13998f"),
        "20": (790, 20, 170, "20_llm_call", "every model call", "#3b7dd8"),
        "tools": (790, 135, 170, "10 · 11 · 12", "lookup tools", "#e8833a"),
        "qdrant": (790, 250, 170, "Qdrant + bge-m3", "regs_structured · 168", "#7b5cd6"),
        "gem": (1030, 0, 200, "Gemini Flash-Lite", "Regulations · Draft · Vision", "#3b7dd8"),
        "oll": (1030, 70, 200, "Ollama qwen3 4B", "Router (+ local mode)", "#3b7dd8"),
        "csv": (1030, 135, 200, "data/tables/*.csv", "calendar · directory · requests", "#e8833a"),
        "regs": (1030, 250, 200, "01_wf1_index_regs", "built the index (once)", "#7d8794"),
        "04": (1300, 135, 190, "04_wf4_errors", "any crash → errors.jsonl", "#c0392b"),
    }
    links = [("student", "03a", "message / photo"), ("harness", "03b", "POST JSON"), ("03a", "03", ""), ("03b", "03", ""),
             ("03", "20", "Router · agents"), ("03", "tools", "exact facts"), ("03", "qdrant", "retrieve articles"),
             ("20", "gem", ""), ("20", "oll", ""), ("tools", "csv", ""), ("regs", "qdrant", "")]
    h = 46
    out = ['<svg width="1510" height="300" xmlns="http://www.w3.org/2000/svg">']

    def anchor(b, side):
        x, y, w = boxes[b][:3]
        return (x + w, y + h / 2) if side == "r" else (x, y + h / 2)

    for a, b, lab in links:
        if b == "qdrant" and a == "regs":
            (x1, y1), (x2, y2) = anchor("regs", "l"), anchor("qdrant", "r")
        elif boxes[a][0] < boxes[b][0]:
            (x1, y1), (x2, y2) = anchor(a, "r"), anchor(b, "l")
        else:
            (x1, y1), (x2, y2) = anchor(a, "l"), anchor(b, "r")
        d = (x2 - x1) / 2
        out.append(f'<path d="M{x1},{y1} C{x1 + d},{y1} {x2 - d},{y2} {x2},{y2}" class="edge"/>')
        sgn = 1 if x2 > x1 else -1
        out.append(f'<path d="M{x2 - 7 * sgn},{y2 - 4} L{x2},{y2} L{x2 - 7 * sgn},{y2 + 4}" class="arrow"/>')
        if lab:
            out.append(f'<text x="{x2 - 10}" y="{y2 - 8}" class="mlab" style="text-anchor:end">{lab}</text>')
    for x, y, w, lab, sl, col in boxes.values():
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{col}1a" stroke="{col}" stroke-width="2"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + 20}" class="mname">{html.escape(lab)}</text>')
        out.append(f'<text x="{x + w / 2}" y="{y + 36}" class="msub">{html.escape(sl)}</text>')
    out.append('<text x="1395" y="215" class="mlab" style="text-anchor:middle">called by n8n on any error</text>')
    out.append("</svg>")
    return "\n".join(out)


CSS = """
body{margin:0;background:#f4f5f7;font-family:'Segoe UI',system-ui,sans-serif;color:#1d2330}
.page{width:2480px;padding:28px 32px 20px}
h1{font-size:30px;margin:0}
.lead{color:#566070;font-size:15px;margin:4px 0 16px}
.card{background:#fff;border:1px solid #dfe3ea;border-radius:12px;padding:12px 16px 4px;margin-bottom:14px}
.head{display:flex;align-items:baseline;gap:12px}
.name{font-weight:700;font-size:17px;font-family:Consolas,monospace}
.badge{font-size:12px;font-weight:600;color:#fff;border-radius:20px;padding:2px 10px}
.role{color:#566070;font-size:13.5px}
.grid{display:flex;flex-wrap:wrap;gap:0 14px}.grid .card{flex:0 0 auto;max-width:min-content}
.card .head{flex-wrap:wrap}
.section{font-size:13px;font-weight:700;letter-spacing:.08em;color:#8a93a3;text-transform:uppercase;margin:6px 0 8px}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:#566070;margin-bottom:14px}
.legend span{display:flex;align-items:center;gap:6px}
.legend i{display:inline-block;width:14px;height:14px;border-radius:4px;border:2px solid}
.foot{color:#8a93a3;font-size:12.5px;margin-top:6px}
svg text{font-family:'Segoe UI',system-ui,sans-serif}
.edge{fill:none;stroke:#9aa3b2;stroke-width:1.6}.arrow{fill:none;stroke:#9aa3b2;stroke-width:1.6}
.tag{font-size:12px;font-weight:800;text-anchor:middle}
.lab{font-size:11.5px;text-anchor:middle;fill:#2b3240}
.sub{font-size:10.5px;font-weight:600;text-anchor:middle}
.elab{font-size:10px;font-weight:600}.elab.true{fill:#2e9e5b}.elab.false{fill:#9aa3b2}.elab.error{fill:#c0392b}
.rowt{font-size:12.5px;font-weight:700;fill:#13998f}.sep{stroke:#e6e9ef;stroke-dasharray:4 4}
.mname{font-size:13.5px;font-weight:700;text-anchor:middle;font-family:Consolas,monospace!important}
.msub{font-size:11.5px;text-anchor:middle;fill:#566070}.mlab{font-size:11px;fill:#566070;text-anchor:middle}
"""


def main():
    wfs = {}
    for f in WF.glob("*.json"):
        w = json.loads(f.read_text(encoding="utf-8"))
        w = w[0] if isinstance(w, list) else w
        wfs[w["name"]] = w
    names = {w["id"]: n for n, w in wfs.items()}

    def card(key, status, role):
        svg, _ = panel_svg(wfs[key], names)
        label, col = STATUS[status]
        n = len(wfs[key]["nodes"])
        return (f'<div class="card"><div class="head"><span class="name">{key}</span>'
                f'<span class="badge" style="background:{col}">{label}</span><span class="role">{n} nodes · '
                f'{html.escape(role)}</span></div>{svg}</div>')

    c = {k: card(k, s, r) for k, s, r in PANELS}
    legend = "".join(f'<span><i style="border-color:{col};background:{col}22"></i>{lab}</span>' for lab, col in [
        ("trigger / entrance", COLORS["trigger"]), ("JavaScript (tested lib code)", COLORS["code"]),
        ("IF decision", COLORS["if"]), ("calls another workflow", COLORS["call"]),
        ("HTTP: Gemini · Ollama · Qdrant", COLORS["http"]), ("Telegram", COLORS["telegram"]),
        ("file read / write", COLORS["file"])])
    used = {k for k, _, _ in PANELS}
    hidden = ", ".join(sorted(n for n in wfs if n not in used))
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>CampusFlow AI workflows</title>
<style>{CSS}</style></head><body><div class="page">
<h1>CampusFlow AI · n8n workflows</h1>
<div class="lead">{len(used)} workflows of the running system, drawn from <b>workflows/*.json</b> exactly as in n8n
(same nodes, same links). Hybrid mode: Router and tools local; Regulations, Draft and Vision on Gemini (ADR-010).</div>
<div class="section">How the workflows call each other</div>
<div class="card" style="padding:14px 16px">{system_map()}</div>
<div class="legend">{legend}</div>
<div class="section">Entrances</div>
<div class="grid g2">{c['03a_wf3_telegram']}{c['03b_wf3_test']}</div>
<div class="section">Core: the assistant</div>
{c['03_wf3_assistant']}
<div class="section">Called by the assistant</div>
<div class="grid g4">{c['20_llm_call']}{c['10_tool_lookup_exam']}{c['11_tool_lookup_contact']}{c['12_tool_lookup_request']}</div>
<div class="section">Support</div>
<div class="grid g3">{c['04_wf4_errors']}{c['01_wf1_index_regs']}{c['02_wf2_tables_check']}</div>
<div class="foot">Not shown (early tests, unpublished): {html.escape(hidden)}. Regenerate: scripts/diagrams/workflows_map.py</div>
</div></body></html>"""
    out_html = OUT / "workflows_map.html"
    out_html.write_text(page, encoding="utf-8")
    print("wrote", out_html.relative_to(ROOT))

    browser = next((p for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                shutil.which("msedge") or "", shutil.which("chrome") or ""] if p and Path(p).exists()), None)
    if not browser:
        sys.exit("no Edge/Chrome found: open the HTML and take a screenshot instead")
    png = OUT / "workflows_map.png"
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--screenshot={png}", "--window-size=2544,4400", out_html.as_uri()],
                   check=True, capture_output=True, timeout=120)
    img = Image.open(png).convert("RGB")
    bg = Image.new("RGB", img.size, img.getpixel((img.width - 1, img.height - 1)))
    box = ImageChops.difference(img, bg).getbbox()
    img.crop((0, 0, img.width, min(img.height, box[3] + 40))).save(png, optimize=True)
    print("wrote", png.relative_to(ROOT), Image.open(png).size)


if __name__ == "__main__":
    main()
