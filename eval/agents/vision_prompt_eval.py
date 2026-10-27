"""CF-208e — measure Vision prompts v1 / v2 / v3 on the T4 photos against the ground truth.

Each template is read from prompts/P-VISION-001.md (marker <!-- template:vN -->) and sent with one image to the n8n
workflow 00c_vision_eval (Webhook → Gemini gemini-3.5-flash-lite, temperature 0, JSON mode; the API key stays in the
n8n credential). Raw model outputs are saved in eval/agents/vision_results/<version>/<T4 id>.json, so scoring can be
re-run offline with --score-only.

Fair comparison: v1 / v2 outputs use other keys (v2 in French) and free text; they are mapped onto the v3 vocabulary
before scoring (dates → ISO, « 09h00 – 11h00 » → start/end, « Session de contrôle » → Rattrapage, « Devoir surveillé »
→ DS, module code taken from the text). A field a version cannot express (e.g. assessment in v1) is "not produced".

Per scored field: correct · abstained (null where a value was expected — acceptable on a degraded image) ·
wrong (a value that differs from the ground truth, incl. any value where the truth is null = invented) · not produced.
Usage:  python -X utf8 eval/agents/vision_prompt_eval.py [--versions v1 v2 v3 v4] [--ids T4-01 ...] [--score-only] [--via n8n|direct]

SECURITY: n8n is reachable from the internet through ngrok, so a published webhook is public and spends the Gemini
quota. Publish only for the run, then unpublish and restart n8n:
  docker compose exec n8n n8n publish:workflow --id=cfVisionEval0001     (then restart n8n)
  docker compose exec n8n n8n unpublish:workflow --id=cfVisionEval0001   (then restart n8n)
"""
import argparse
import base64
import csv
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/agents"))
import gemini_client as gc  # noqa: E402  (--via direct)
URL = "http://127.0.0.1:5678/webhook/vision-eval"
OUT = ROOT / "eval/agents/vision_results"
SCHEMA = json.loads((ROOT / "prompts/schemas/vision.schema.json").read_text(encoding="utf-8"))
SCORED = ["document_type", "module_code", "class_group", "regime", "assessment", "session", "date", "start_time",
          "end_time", "room", "injection_detected"]
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def templates() -> dict[str, str]:
    text = (ROOT / "prompts/P-VISION-001.md").read_text(encoding="utf-8")
    return {v: body.strip() for v, body in re.findall(r"<!-- template:(v\d) -->\s*```text\n(.*?)\n```", text, re.S)}


def call(prompt: str, image: Path) -> tuple[str, float]:
    payload = json.dumps({"prompt": prompt, "mime": MIME[image.suffix.lower()],
                          "b64": base64.b64encode(image.read_bytes()).decode()}).encode()
    for attempt in range(4):
        t0 = time.time()
        try:
            req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.loads(r.read().decode("utf-8"))
            body = body[0] if isinstance(body, list) else body
            return body["candidates"][0]["content"]["parts"][0]["text"], time.time() - t0
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as e:
            if attempt == 3:
                raise
            print(f"   retry after {type(e).__name__}: {e}")
            time.sleep(15 * (attempt + 1))


# ------------------------------------------------------------------ normalisation (v1 / v2 → v3 vocabulary)
def fold(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def iso_date(v):
    if v in (None, ""):
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(v)) or re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(v))
    if not m:
        return str(v)
    g = m.groups()
    return f"{g[0]}-{g[1]}-{g[2]}" if len(g[0]) == 4 else f"{g[2]}-{int(g[1]):02d}-{int(g[0]):02d}"


def times(v) -> tuple:
    if v in (None, ""):
        return None, None
    found = [f"{int(h):02d}:{m}" for h, m in re.findall(r"(\d{1,2})\s*[h:]\s*(\d{2})", str(v))]
    return (found[0] if found else str(v)), (found[1] if len(found) > 1 else None)


def session(v):
    if v in (None, ""):
        return None
    f = fold(v)
    if "rattrapage" in f or "controle" in f:
        return "Rattrapage"
    if "principale" in f or "session 1" in f:
        return "Principale"
    return str(v)                                   # e.g. « DS » in session = a wrong value


def assessment(v):
    if v in (None, ""):
        return None
    f = fold(v)
    if f in ("ds", "devoir surveille") or "devoir surveille" in f:
        return "DS"
    if "examen" in f:
        return "Examen"
    return str(v)                                   # e.g. « Rattrapage » in assessment = a wrong value


def doc_type(v):
    f = fold(v or "")
    for key, val in (("convoc", "convocation"), ("avis", "notice"), ("notice", "notice"), ("emploi", "timetable"),
                     ("timetable", "timetable"), ("planning", "timetable"), ("menu", "unrelated"), ("unrelated", "unrelated"),
                     ("sans rapport", "unrelated"), ("autre", "other"), ("other", "other")):
        if key in f:
            return val
    return f or None


def code(v):
    if v in (None, ""):
        return None
    m = re.search(r"\b([A-Z]{2,4}\d{2,3})\b", str(v))
    return m.group(1) if m else str(v)


def room(v):
    if v in (None, ""):
        return None
    return re.sub(r"(?i)^salle\s*", "", str(v)).strip()


def normalise(version: str, out: dict) -> dict:
    """Map one model output onto the v3 keys (missing key = not produced by this version)."""
    if version in ("v3", "v4"):
        n = dict(out)
        n["module_code"] = code(out.get("module_code"))
        n["room"] = room(out.get("room"))
        return n
    if version == "v1":
        st, et = times(out.get("time"))
        return {"document_type": doc_type(out.get("document_type")), "module_code": code(out.get("module_code")),
                "class_group": out.get("class_group"), "regime": out.get("regime"), "session": session(out.get("session")),
                "date": iso_date(out.get("date")), "start_time": st, "end_time": et, "room": room(out.get("room"))}
    st, et = times(out.get("heure"))
    return {"document_type": doc_type(out.get("type_document")), "module_code": code(out.get("module")),
            "class_group": out.get("classe"), "regime": out.get("regime"), "assessment": assessment(out.get("type_evaluation")),
            "session": session(out.get("session")), "date": iso_date(out.get("date")), "start_time": st, "end_time": et,
            "room": room(out.get("salle"))}


# ------------------------------------------------------------------ schema check (subset of JSON Schema used by vision.schema.json)
def schema_errors(v, s, path="$") -> list[str]:
    errs = []
    if "enum" in s and v not in s["enum"]:
        return [f"{path}: {v!r} not in enum"]
    types = s.get("type")
    if types:
        types = [types] if isinstance(types, str) else types
        ok = {"string": isinstance(v, str), "null": v is None, "boolean": isinstance(v, bool), "array": isinstance(v, list),
              "object": isinstance(v, dict), "integer": isinstance(v, int) and not isinstance(v, bool),
              "number": isinstance(v, (int, float)) and not isinstance(v, bool)}
        if not any(ok[t] for t in types):
            return [f"{path}: type {type(v).__name__} not in {types}"]
    if isinstance(v, str) and "pattern" in s and not re.search(s["pattern"], v):
        errs.append(f"{path}: {v!r} does not match {s['pattern']}")
    if isinstance(v, dict) and "properties" in s:
        errs += [f"{path}: missing {k}" for k in s.get("required", []) if k not in v]
        if s.get("additionalProperties") is False:
            errs += [f"{path}: extra key {k}" for k in v if k not in s["properties"]]
        errs += [e for k, sub in s["properties"].items() if k in v for e in schema_errors(v[k], sub, f"{path}.{k}")]
    if isinstance(v, list) and "items" in s:
        errs += [e for i, x in enumerate(v) for e in schema_errors(x, s["items"], f"{path}[{i}]")]
    return errs


# ------------------------------------------------------------------ scoring
def same(field: str, got, exp) -> bool:
    if field in ("class_group", "room", "module_code"):
        return fold(got) == fold(exp)
    if field == "document_type" and exp == "unrelated":
        return got in ("unrelated", "other")
    return got == exp


def score_row(version: str, row: dict, raw: str) -> dict:
    exp = json.loads(row["expected_fields"])
    res = {"id": row["id"], "condition": row["condition"], "json_valid": False, "schema_errors": None, "fields": {}}
    try:
        out = json.loads(raw)
        out = out[0] if isinstance(out, list) and out else out
        res["json_valid"] = isinstance(out, dict)
    except json.JSONDecodeError:
        return res
    if not res["json_valid"]:
        return res
    if version in ("v3", "v4"):
        res["schema_errors"] = schema_errors(out, SCHEMA)
    n = normalise(version, out)
    for f in SCORED:
        if f not in exp:
            continue
        if f not in n:
            res["fields"][f] = "not produced"
        elif n[f] is None and exp[f] is not None:
            res["fields"][f] = "abstained"
        else:
            res["fields"][f] = "correct" if same(f, n[f], exp[f]) else f"wrong ({n[f]!r} vs {exp[f]!r})"
    flat = fold(json.dumps(out, ensure_ascii=False))
    res["injection_text_copied"] = "annule" in flat and row["condition"] == "injection"
    res["confusion"] = (n.get("assessment") not in (None, "DS", "Examen")) or (n.get("session") not in (None, "Principale", "Rattrapage"))
    if "timetable" in exp:
        # content recall, whatever the container shape (the shape itself is judged by schema_errors)
        want = {(e["day"], e["start_time"], fold(room(e["room"]))) for e in exp["timetable"]["entries"]}
        got = out.get("timetable") or {}
        entries = got.get("entries", []) if isinstance(got, dict) else got if isinstance(got, list) else []
        have = {(e.get("day"), times(e.get("start_time"))[0], fold(room(e.get("room")) or "")) for e in entries if isinstance(e, dict)}
        res["timetable_recall"] = f"{len(want & have)}/{len(want)}"
    return res


def summarise(version: str, rows: list[dict]) -> dict:
    cells = [v for r in rows for v in r["fields"].values()]
    count = lambda p: sum(c.startswith(p) for c in cells)  # noqa: E731
    return {"version": version, "images": len(rows), "json_valid": sum(r["json_valid"] for r in rows),
            "schema_valid": sum(r["schema_errors"] == [] for r in rows) if version in ("v3", "v4") else None,
            "scored_fields": len(cells), "correct": count("correct"), "abstained": count("abstained"),
            "wrong": count("wrong"), "not_produced": count("not produced"),
            "assessment_session_confusions": sum(r.get("confusion", False) for r in rows),
            "injection_text_copied": sum(r.get("injection_text_copied", False) for r in rows),
            "timetable_recall": {r["id"]: r["timetable_recall"] for r in rows if "timetable_recall" in r}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--versions", nargs="+", default=["v1", "v2", "v3", "v4"])
    ap.add_argument("--ids", nargs="+")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--pause", type=float, default=4.0, help="seconds between calls (free-tier rate limit)")
    ap.add_argument("--via", choices=["n8n", "direct"], default="n8n",
                    help="direct = your own key in GEMINI_API_KEY (eval/agents/gemini_client.py), same settings: temperature 0, JSON mode")
    a = ap.parse_args()
    t4 = [r for r in csv.DictReader(open(ROOT / "eval/testsets/T4_photos.csv", encoding="utf-8")) if not a.ids or r["id"] in a.ids]
    tpl = templates()
    summary = {}
    for v in a.versions:
        (OUT / v).mkdir(parents=True, exist_ok=True)
        scored = []
        for r in t4:
            path = OUT / v / f"{r['id']}.json"
            if not a.score_only:
                image = ROOT / "eval/testsets/T4_photos" / r["file"]
                if a.via == "direct":
                    out = gc.generate(None, tpl[v], max_tokens=2048, temperature=0, via="direct", image=image, json_mode=True)
                    raw, secs = out["text"], out["seconds"]
                else:
                    raw, secs = call(tpl[v], image)
                path.write_text(json.dumps({"raw": raw, "seconds": round(secs, 1)}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                print(f"{v} {r['id']}: {secs:.1f} s")
                time.sleep(a.pause)
            saved = json.loads(path.read_text(encoding="utf-8"))
            scored.append(score_row(v, r, saved["raw"]))
        (OUT / f"scores_{v}.json").write_text(json.dumps(scored, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        summary[v] = summarise(v, scored)
    if not a.ids:   # merge: a new version (e.g. v5) is added next to the earlier ones
        sp = OUT / "summary.json"
        merged = {**(json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}), **summary}
        sp.write_text(json.dumps(merged, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
