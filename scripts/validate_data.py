"""CF-110 — validate the Phase 1 dataset (tables, corpus, test sets, cross-file links, labelling, privacy).

Run: .venv/Scripts/python scripts/validate_data.py      → prints one line per check; exit code 1 if any ERROR.
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from corpus_lookup import CLEAN, all_doc_ids, article_keys, doc, longest_shared_run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "data/tables"
REGIME_RE = re.compile(r"^(all|(jour|soir|alternance)(;(jour|soir|alternance))*)$")  # A3
EMAIL_RE = re.compile(r"^[a-z0-9._-]+@(esprit\.tn|esprit\.example)$")
NO_SRC = "FICTITIOUS — no source"
results = []


def check(name: str, ok: bool, detail: str = "", level: str = "ERROR") -> None:
    results.append(("PASS" if ok else level, name, detail))


def read(p: Path) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


def regime_ok(v: str) -> bool:
    parts = v.split(";")
    return bool(REGIME_RE.match(v)) and len(parts) == len(set(parts))


# ---------------------------------------------------------------- corpus
ids = all_doc_ids()
check("corpus: 13 cleaned documents D1-001…D1-013 (D1-012/013 authored, CF-117)", ids == [f"D1-{i:03d}" for i in range(1, 14)], str(ids))
for i in ids:
    d = doc(i)
    full = "\n".join(p["text"] for p in d["pages"])
    keys = [u["key"] for u in d["articles"]]
    check(f"{i}: regime value valid (A3)", regime_ok(d["regime"]), d["regime"])
    check(f"{i}: doc_status official|FICTITIOUS", d["doc_status"] in ("official", "FICTITIOUS"), d["doc_status"])
    check(f"{i}: no (cid:N) glyphs", "(cid:" not in full)
    check(f"{i}: no synthetic footers", not re.search(r"ESPRIT-[A-Z]+-\d+\s*\|.*Page\s*\d", full))
    check(f"{i}: no table-of-contents lines", not re.search(r"^\s*(Article\s*\d+|CHAPITRE\s+[IVXL]+).*(\.{4,}|…{2,})", full, re.M | re.I))
    check(f"{i}: article keys unique", len(keys) == len(set(keys)), str([k for k in keys if keys.count(k) > 1]))
    check(f"{i}: at least one article", any(u["level"] == "article" for u in d["articles"]))
    pdf = ROOT / "data/regs" / d["file"]
    if d["doc_status"] == "FICTITIOUS":
        check(f"{i}: file name ends with _FICTIF.pdf", d["file"].endswith("_FICTIF.pdf"), d["file"])
        check(f"{i}: regenerated FICTIF PDF present (CF-104)", pdf.exists(), str(pdf.name), level="PENDING")
        if pdf.exists():
            from pypdf import PdfReader
            r = PdfReader(str(pdf))
            label = all("DOCUMENT FICTIF" in (p.extract_text() or "") for p in r.pages)
            check(f"{i}: 'DOCUMENT FICTIF' on every page", label)
            check(f"{i}: metadata title starts with [FICTIF]", str((r.metadata or {}).get("/Title", "")).startswith("[FICTIF]"))
            check(f"{i}: every chunk text carries the FICTIF label", all(u["text"].startswith("[DOCUMENT FICTIF") for u in d["articles"]))
    else:
        from pypdf import PdfReader
        check(f"{i}: cleaned PDF present", pdf.exists(), str(pdf.name))
        if pdf.exists():
            check(f"{i}: no /Author metadata", "/Author" not in (PdfReader(str(pdf)).metadata or {}))
KEYS = article_keys()

# ---------------------------------------------------------------- D2 calendar
cal = read(T / "exam_calendar.csv")
mods = read(T / "module_codes.csv")
COLS2 = ["exam_id", "module_code", "module_name", "module_name_norm", "class_group", "semester", "session", "exam_type",
         "assessment", "date", "start_time", "end_time", "room", "last_updated", "data_status"]
check("D2: columns exactly as specified", list(cal[0].keys()) == COLS2, str(list(cal[0].keys())))
check("D2: exam_id unique", len({r["exam_id"] for r in cal}) == len(cal))
allowed = {"semester": {"S1", "S2"}, "session": {"Principale", "Rattrapage"},
           "exam_type": {"Written", "Oral", "Practical", "Project defence", "Certification"},
           "assessment": {"DS", "Examen"}, "data_status": {"projected from 2025-2026", "FICTITIOUS"}}
for c, vals in allowed.items():
    bad = sorted({r[c] for r in cal} - vals)
    check(f"D2: {c} values allowed", not bad, str(bad))
check("D2: dates YYYY-MM-DD", all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]) for r in cal))
check("D2: start_time HH:MM", all(re.fullmatch(r"\d{2}:\d{2}", r["start_time"]) for r in cal))
check("D2: end_time empty or HH:MM after start", all(not r["end_time"] or (re.fullmatch(r"\d{2}:\d{2}", r["end_time"]) and r["end_time"] > r["start_time"]) for r in cal))
proj = [r for r in cal if r["data_status"] != "FICTITIOUS"]
fict = [r for r in cal if r["data_status"] == "FICTITIOUS"]
check("D2: projected rows never carry an invented room or end_time", all(not r["room"] and not r["end_time"] for r in proj), f"{len(proj)} rows")
check("D2: FICTITIOUS demo rows have room and end_time", fict and all(r["room"] and r["end_time"] for r in fict), f"{len(fict)} rows")
check("D2: demo case DS14 / 5DS6 / 2027-01-15 / 09:00-11:00 / B12 present",
      any((r["module_code"], r["class_group"], r["date"], r["start_time"], r["end_time"], r["room"]) == ("DS14", "5DS6", "2027-01-15", "09:00", "11:00", "B12") for r in cal))
check("D2: Rattrapage rows present", any(r["session"] == "Rattrapage" for r in cal))
check("D2: last_updated filled (YYYY-MM-DD)", all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["last_updated"]) for r in cal))
check("D2: module_name_norm = normalise(module_name) (A7)", all(r["module_name_norm"] == norm(r["module_name"]) for r in cal))
mod_codes = {m["module_code"]: m["module_name"] for m in mods}
check("D2 → module_codes: every module_code mapped to its name", all(mod_codes.get(r["module_code"]) == r["module_name"] for r in cal))
check("module_codes: codes unique", len(mod_codes) == len(mods))

# ---------------------------------------------------------------- D3 directory
dr = read(T / "directory.csv")
COLS3 = ["role_id", "role_title", "department", "person_name", "email", "office", "hours", "handles", "reports_to",
         "escalation_level", "level_scope", "source"]
check("D3: columns (spec D3 + level_scope, source)", list(dr[0].keys()) == COLS3, str(list(dr[0].keys())))
roles = {r["role_id"]: r for r in dr}
check("D3: role_id unique", len(roles) == len(dr))
check("D3: >= 12 roles", len(dr) >= 12, str(len(dr)))
check("D3: every reports_to exists", all(not r["reports_to"] or r["reports_to"] in roles for r in dr))
roots = [r["role_id"] for r in dr if not r["reports_to"]]
check("D3: exactly one root", len(roots) == 1, str(roots))
cyc = []
for k in roles:
    seen, x = set(), k
    while roles[x]["reports_to"]:
        if x in seen:
            cyc.append(k); break
        seen.add(x); x = roles[x]["reports_to"]
check("D3: no cycles", not cyc, str(cyc))
check("D3: e-mails role-based on esprit.tn / esprit.example", all(EMAIL_RE.match(r["email"]) for r in dr))
check("D3: invented roles use esprit.example (P3)", all(r["email"].endswith("@esprit.example") == r["source"].startswith("FICTITIOUS — invented") for r in dr))
check("D3: person_name empty (no personal data)", all(not r["person_name"] for r in dr))
check("D3: department filled", all(r["department"] for r in dr))
for need in ("COORD-DS", "VIE-ETU", "IT-SUP"):
    check(f"D3: role {need} present", need in roles)

# ---------------------------------------------------------------- D4 requests
rq = read(T / "request_catalogue.csv")
COLS4 = ["request_type", "handler_role_id", "required_documents", "deadline_rule", "source_ref", "regime", "request_id",
         "category", "routing_rule", "processing_time", "source"]
check("D4: columns (spec D4 + regime + extras)", list(rq[0].keys()) == COLS4, str(list(rq[0].keys())))
check("D4: request_id unique", len({r["request_id"] for r in rq}) == len(rq))
check("D4: >= 6 request types", len(rq) >= 6, str(len(rq)))
check("D4: regime values valid (A3)", all(regime_ok(r["regime"]) for r in rq), str(sorted({r["regime"] for r in rq})))
bad_h = sorted({r["handler_role_id"] for r in rq if r["handler_role_id"] not in roles and r["handler_role_id"] != "SCO-LEVEL"})
check("D4 → D3: every handler exists (SCO-LEVEL whitelisted)", not bad_h, str(bad_h))
check("D4: SCO-LEVEL rows document their routing rule", all("niveau" in r["routing_rule"] for r in rq if r["handler_role_id"] == "SCO-LEVEL"))
# SCO-LEVEL is resolved from the first digit of the class group: 5DS6 → level 5 → SCO-5A
check("D3: SCO-LEVEL resolvable for levels 1-5 (e.g. 5DS6 → SCO-5A)", all(f"SCO-{n}A" in roles for n in range(1, 6)))
cal_levels = sorted({r["class_group"][0] for r in cal})
check("D2 → D3: every calendar class level has a SCO-<n>A service", all(f"SCO-{n}A" in roles for n in cal_levels), str(cal_levels))
bad_ref = [(r["request_id"], k) for r in rq if r["source_ref"] != NO_SRC for k in r["source_ref"].split(" | ") if k not in KEYS]
check("D4 → corpus: every source_ref is an existing article key", not bad_ref, str(bad_ref))
unlabelled = [r["request_id"] for r in rq if (r["source_ref"] == NO_SRC or all(k.split("/")[0] >= "D1-004" for k in r["source_ref"].split(" | "))) and "FICTITIOUS" not in r["source"]]
check("D4: rows without an official source are labelled FICTITIOUS", not unlabelled, str(unlabelled))
PHRASE = re.compile(r"(\d+\s*(?:jours? ouvrables?|jours?|heures|h|semaines?|mois)\b|\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)|une semaine|lendemain)", re.I)
hnorm = lambda s: re.sub(r"(\d+)\s*h\b", r"\1 heures", re.sub(r"\s+", " ", s.replace("’", "'").lower()))
two_versions = []
for r in rq:
    if r["source_ref"] == NO_SRC:
        continue
    cited = hnorm(" ".join(next(u["text"] for u in doc(k.split("/")[0])["articles"] if u["key"] == k) for k in r["source_ref"].split(" | ")))
    for field in ("deadline_rule", "processing_time"):
        for ph in PHRASE.findall(r[field]):
            if hnorm(ph) not in cited and not ("catalogue only" in r["source"] and (field in r["source"] or "délai" in r["source"])):
                two_versions.append((r["request_id"], field, ph))
check("D4 → corpus: every duration/date in deadline_rule / processing_time appears in the cited articles (no second version)",
      not two_versions, str(two_versions))
check("D4: REQ-08 split by regime (REQ-08-J jour / REQ-08-SA soir;alternance)",
      {(r["request_id"], r["regime"]) for r in rq if r["request_id"].startswith("REQ-08")} == {("REQ-08-J", "jour"), ("REQ-08-SA", "soir;alternance")})

# ---------------------------------------------------------------- test sets
t1p = ROOT / "eval/testsets/T1_regulations.csv"
if t1p.exists():
    t1 = read(t1p)
    check("T1: 25 rows", len(t1) == 25, str(len(t1)))
    check("T1: columns", list(t1[0].keys()) == ["id", "question", "regime", "topic", "expected_doc_id", "expected_article",
                                                 "expected_page", "expected_answer", "answerable", "verified_by"])
    check("T1: regime values valid (A3)", all(regime_ok(r["regime"]) for r in t1))
    missing = [(r["id"], k) for r in t1 if r["answerable"] == "yes" for k in r["expected_article"].split("|") if k not in KEYS]
    check("T1: every expected_article key exists in data/regs/clean (A4)", not missing, str(missing))
    check("T1: expected_doc_id consistent with the keys", all(set(r["expected_doc_id"].split("|")) == {k.split("/")[0] for k in r["expected_article"].split("|")} for r in t1 if r["answerable"] == "yes"))
    copied = []
    for r in t1:
        if r["answerable"] == "yes":
            for k in r["expected_article"].split("|"):
                d_id = k.split("/")[0]
                unit = next(u["text"] for u in doc(d_id)["articles"] if u["key"] == k)
                n = longest_shared_run(r["question"], unit)
                if n > 5:
                    copied.append((r["id"], n))
    check("T1: no question reuses > 5 consecutive words of its source (A5)", not copied, str(copied))
    check("T1: 3 unanswerable rows", sum(r["answerable"] == "no" for r in t1) == 3)
    nver = sum(bool(r["verified_by"]) for r in t1)
    check("T1: all 25 rows verified by Fedi", nver == 25, f"{nver}/25 verified", level="PENDING")
    # CF-208a: these two checks sat under `else:` (ran only when T1 was missing); they belong to the T1 branch
    sys.path.insert(0, str(ROOT / "eval/retrieval"))
    import retrieval_metrics as rm
    try:
        rm.self_test(); mt = True
    except AssertionError:
        mt = False
    check("eval/retrieval/retrieval_metrics.py: Hit@5 / Recall@5 / MRR self-test on '|'-separated key lists", mt)
    check("T1: multi-source rows parse into existing keys", all(all(k in KEYS for k in rm.parse_expected(r["expected_article"])) for r in t1))
else:
    check("T1 present", False, level="PENDING")
for name, n in [("T2_calendar.csv", 12), ("T3_contacts_requests.csv", 10), ("T5_adversarial.csv", 6), ("T4_photos.csv", 11)]:
    p = ROOT / "eval/testsets" / name
    check(f"{name}: {n} rows", p.exists() and len(read(p)) == n, f"{len(read(p)) if p.exists() else 0} rows", level="PENDING" if not p.exists() else "ERROR")
p2 = ROOT / "eval/testsets/T2_calendar.csv"
if p2.exists():
    calkeys = {(r["class_group"], r["module_name"], r["session"]) for r in cal}
    t2 = read(p2)
    NP = "non communiqué (pas encore publié)"
    unpublished = [r for r in t2 if r["expected_date"] == NP]
    bad_np = [r["id"] for r in unpublished if (r["class_group"], r["module"], r["session"]) in calkeys
              or (r["class_group"], r["module"], "Principale") not in calkeys]
    check("T2: 'pas encore publié' rows = existing exam whose retake is not in the calendar", not bad_np, str(bad_np))
    found = [r for r in t2 if r["expected_date"] not in ("not found", NP)]
    bad = [r["id"] for r in found if (r["class_group"], r["module"], r["session"]) not in calkeys]
    check("T2 → D2: referenced (class, module, session) exist", not bad, str(bad))
    ghost = [r["id"] for r in t2 if r["expected_date"] == "not found" and (r["class_group"], r["module"], r["session"]) in calkeys]
    check("T2: 'not found' rows really absent from the calendar", not ghost, str(ghost))
    proj = {(r["class_group"], r["module_name"], r["session"]) for r in cal if r["data_status"] != "FICTITIOUS"}
    inv = [r["id"] for r in found if (r["class_group"], r["module"], r["session"]) in proj and (r["expected_room"] != "non communiqué" or r["expected_end_time"] != "non communiqué")]
    check("T2: projected rows expect 'non communiqué' for room and end time", not inv, str(inv))
p3 = ROOT / "eval/testsets/T3_contacts_requests.csv"
if p3.exists():
    t3 = read(p3)
    bad = [r["id"] for r in t3 if r["expected_role_id"] not in roles]
    check("T3 → D3: expected_role_id exist", not bad, str(bad))
    bad = [r["id"] for r in t3 if r["expected_role_id"] in roles and r.get("email_status") !=
           ("FICTITIOUS" if roles[r["expected_role_id"]]["email"].endswith("@esprit.example") else "delivered (unverified)")]
    check("T3: email_status matches the contact (delivered (unverified) | FICTITIOUS)", not bad, str(bad))
    NAMES = {"jour": "cours du jour", "soir": "cours du soir", "alternance": "alternance"}
    other = [(r["id"], n) for r in t3 if r["regime"] != "all" for reg, n in NAMES.items()
             if reg not in r["regime"].split(";") and n in (r["expected_documents"] + " " + r["expected_deadline"]).lower()]
    check("T3: expected values mention no other regime than the question's (regime-specific)", not other, str(other))
p4 = ROOT / "eval/testsets/T4_photos.csv"
if p4.exists():
    t4 = read(p4)
    miss = [r["file"] for r in t4 if not (ROOT / "eval/testsets/T4_photos" / r["file"]).exists()]
    check("T4: every image file present", not miss, str(miss))
    vkeys = set(json.loads((ROOT / "prompts/schemas/vision.schema.json").read_text(encoding="utf-8"))["properties"])
    badk = [(r["id"], k) for r in t4 for k in json.loads(r["expected_fields"]) if k not in vkeys]
    check("T4: expected_fields use the Vision schema keys (prompts/schemas/vision.schema.json)", not badk, str(badk))
    check("T4: covers blurry, rotated, hidden field, injection and unrelated",
          {"blurry", "rotated", "hidden field", "injection", "unrelated"} <= {r["condition"] for r in t4}, str(sorted({r["condition"] for r in t4})))
    der = [r["id"] for r in t4 if r["derived_from"] and r["derived_from"] not in {x["file"] for x in t4}]
    check("T4: derived images point to a T4 source image", not der, str(der))
t5p = ROOT / "eval/testsets/T5_adversarial.csv"
ref = [(r["id"], m) for r in read(t5p) for m in re.findall(r"photo (T4-\d\d)", r["question_or_input"])
       if not any(x["id"] == m for x in (read(p4) if p4.exists() else []))]
check("T5 → T4: referenced photos exist in T4", not ref, str(ref))
unticked = {n: [r.get("id") or r["file"] for r in read(ROOT / f"eval/testsets/{n}.csv") if not r["verified_by"]]
            for n in ("T2_calendar", "T3_contacts_requests", "T4_photos", "T5_adversarial") if (ROOT / f"eval/testsets/{n}.csv").exists()}
check("T2–T5: every row ticked by Fedi", not any(unticked.values()), str({k: v for k, v in unticked.items() if v}), level="PENDING")

# ---------------------------------------------------------------- D5 candidates (CF-208b)
stray = [p.relative_to(ROOT).as_posix() for p in list((ROOT / "eval").glob("D5*")) + list((ROOT / "eval/testsets").glob("D5*"))]
check("D5: never stored as a test set (only under eval/candidates/)", not stray, str(stray))
p5 = ROOT / "eval/candidates/D5_triage.csv"
if p5.exists():
    d5 = read(p5)
    STATUSES = {"leak", "rule_conflict", "blocked_source", "route_only", "supported"}
    check("D5 triage: unique D5-NNN ids", len({r["d5_id"] for r in d5}) == len(d5) and all(re.fullmatch(r"D5-\d{3}", r["d5_id"]) for r in d5))
    check("D5 triage: every row has a status and a reason unless supported / route_only",
          all(r["status"] in STATUSES and (r["reasons"] or r["status"] == "supported") for r in d5))
    check("D5 triage: leaked questions are excluded from the Router dev set", all(r["router_dev"] == "no" for r in d5 if r["status"] == "leak"))
    bad_int = [r["d5_id"] for r in d5 if not set(r["router_intents"].split(";")) <= {"regulations", "calendar", "admin", "vision", "out_of_scope"}]
    check("D5 triage: router_intents use the Router enum", not bad_int, str(bad_int))
    doc_counts = dict(re.findall(r"^\| `(\w+)` \|.*\| (\d+) \|$", (ROOT / "eval/candidates/README.md").read_text(encoding="utf-8"), re.M))
    real = {s: str(sum(r["status"] == s for r in d5)) for s in STATUSES}
    check("D5 triage: eval/candidates/README.md counts match D5_triage.csv", doc_counts == real, f"README {doc_counts} vs {real}")
else:
    check("D5 triage present (eval/candidates/D5_triage.csv)", False)

# ---------------------------------------------------------------- prompt library (CF-208c)
PR = ROOT / "prompts"
AGENTS = ["ROUTER", "VISION", "REGULATIONS", "CALENDAR", "ADMIN", "COMPOSER", "CRITIC"]
FIELDS = ["**ID**", "**Version**", "**Agent**", "**Role**", "**Technique**", "**Template**", "**Output**",
          "**Failure observed (input)**", "**Fix**", "**Result**"]
lib = {a: PR / f"P-{a}-001.md" for a in AGENTS}
check("prompts: one library file per agent (P-<AGENT>-001.md)", all(p.exists() for p in lib.values()),
      str([p.name for p in lib.values() if not p.exists()]))
nofmt = [(a, f) for a, p in lib.items() if p.exists() for f in FIELDS if f not in p.read_text(encoding="utf-8")]
check("prompts: every entry has the 10 library-format fields", not nofmt, str(nofmt[:6]))
FRENCH_KEYS = {"classe", "salle", "heure", "extrait_utile", "incertitudes", "type_document", "type_evaluation", "module"}
schemas = {p.stem.split(".")[0]: p for p in (PR / "schemas").glob("*.schema.json")} if (PR / "schemas").exists() else {}


def schema_keys(node) -> set[str]:
    """Every property name declared anywhere in a JSON Schema."""
    out = set()
    if isinstance(node, dict):
        out |= set(node.get("properties", {}))
        for v in node.values():
            out |= schema_keys(v)
    elif isinstance(node, list):
        for v in node:
            out |= schema_keys(v)
    return out


bad_schema, fr = [], []
for name, p in schemas.items():
    try:
        keys = schema_keys(json.loads(p.read_text(encoding="utf-8")))
    except json.JSONDecodeError as e:
        bad_schema.append(f"{name}: {e}")
        continue
    fr += [f"{name}.{k}" for k in keys if k in FRENCH_KEYS or not re.fullmatch(r"[a-z][a-z0-9_]*", k)]
check("prompts: a JSON schema per JSON agent (Composer outputs text)",
      set(schemas) == {a.lower() for a in AGENTS} - {"composer"}, str(sorted(schemas)))
check("prompts: schemas parse", not bad_schema, str(bad_schema))
check("prompts: schema keys are English snake_case (no v2 French keys)", not fr, str(fr))


def fence_error(text: str) -> bool:
    """True if a code block opens inside another (```lang while open) or is never closed."""
    inside = False
    for ln in text.splitlines():
        m = re.match(r"\s*```(\S*)", ln)
        if m:
            if inside and m.group(1):
                return True
            inside = not inside
    return inside


fences = [p.relative_to(ROOT).as_posix() for p in PR.rglob("*.md") if fence_error(p.read_text(encoding="utf-8"))]
check("prompts: Markdown code fences balanced, none nested", not fences, str(fences))
named = [p.name for p in PR.rglob("*") if re.search(r"ines|doua|fedi", p.name, re.I)]
check("prompts: no person names in file names", not named, str(named))
rex = PR / "examples/router_examples.md"
if rex.exists():
    rows = [ln.split("|") for ln in rex.read_text(encoding="utf-8").splitlines() if re.match(r"\| R\d\d ", ln)]
    offi = [(r["id"], r.get("question") or r["question_or_input"]) for n in ("T1_regulations", "T2_calendar", "T3_contacts_requests", "T5_adversarial")
            for r in read(ROOT / f"eval/testsets/{n}.csv")]
    lk = [(r[1].strip(), oid) for r in rows for oid, oq in offi if longest_shared_run(r[2], oq) >= 6]
    check("prompts: router examples share < 6 consecutive words with T1–T5", not lk, str(lk))
    cal_mods, cal_cls = {r["module_code"] for r in cal}, {r["class_group"] for r in cal}
    ghost = [(r[1].strip(), m) for r in rows for m in re.findall(r"module_code=([\w-]+)", r[6]) if m not in cal_mods | {"missing"}]
    ghost += [(r[1].strip(), c) for r in rows for c in re.findall(r"class_group=([\w-]+)", r[6]) if c not in cal_cls | {"missing"}]
    check("prompts: router example module codes and classes exist in data/tables", not ghost, str(ghost))
    check("prompts: 30 router examples", len(rows) == 30, str(len(rows)))
else:
    check("prompts: router examples present (prompts/examples/router_examples.md)", False)

# ---------------------------------------------------------------- privacy
texts = list(T.glob("*.csv")) + list((ROOT / "eval").rglob("*.csv")) + list((ROOT / "eval").rglob("*.md")) + list(CLEAN.glob("*.json"))
leaks = []
for p in texts:
    s = p.read_text(encoding="utf-8")
    for e in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", s):
        if not EMAIL_RE.match(e.lower()):
            leaks.append((p.name, e[:2] + "…"))
    if re.search(r"(?:\+216[\s.]?)?\b[2-9]\d[\s.]?\d{3}[\s.]?\d{3}\b", s):
        leaks.append((p.name, "phone-like number"))
check("privacy: no personal e-mails / phone numbers in data, clean corpus and eval files", not leaks, str(leaks[:5]))

# ---------------------------------------------------------------- links (CF-208a)
mds = [ROOT / "README.md"] + [p for d in ("report", "prompts", "eval", "data", "scripts") for p in (ROOT / d).rglob("*.md")]
dead = []
for p in mds:
    for target in re.findall(r"\]\(([^)\s]+)\)", p.read_text(encoding="utf-8")):
        if re.match(r"(https?:|mailto:|#)", target):
            continue
        if not (p.parent / target.split("#")[0]).resolve().exists():
            dead.append(f"{p.relative_to(ROOT).as_posix()} → {target}")
check("links: every relative Markdown link resolves (README, report, prompts, eval, data, scripts)", not dead, str(dead))

# ---------------------------------------------------------------- report
for lvl, name, det in results:
    print(f"{lvl:7} {name}" + (f"  [{det}]" if det and lvl != "PASS" else ""))
err = sum(1 for r in results if r[0] == "ERROR")
pend = sum(1 for r in results if r[0] == "PENDING")
print(f"\n{len(results)} checks: {sum(1 for r in results if r[0] == 'PASS')} pass, {err} error, {pend} pending")
sys.exit(1 if err else 0)
