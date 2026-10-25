"""CF-110 — validate the Phase 1 dataset (tables, corpus, test sets, cross-file links, labelling, privacy).

Run: .venv/Scripts/python scripts/validate_data.py      → prints one line per check; exit code 1 if any ERROR.
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
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
check("corpus: 11 cleaned documents D1-001…D1-011", ids == [f"D1-{i:03d}" for i in range(1, 12)], str(ids))
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
check("D4: REQ-08 split by regime (REQ-08-J jour / REQ-08-SA soir;alternance)",
      {(r["request_id"], r["regime"]) for r in rq if r["request_id"].startswith("REQ-08")} == {("REQ-08-J", "jour"), ("REQ-08-SA", "soir;alternance")})

# ---------------------------------------------------------------- test sets
t1p = ROOT / "eval/T1_regulations.csv"
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
else:
    check("T1 present", False, level="PENDING")
for name, n in [("T2_calendar.csv", 10), ("T3_contacts_requests.csv", 10), ("T5_adversarial.csv", 6), ("T4_photos.csv", 8)]:
    p = ROOT / "eval" / name
    check(f"{name}: {n} rows", p.exists() and len(read(p)) == n, f"{len(read(p)) if p.exists() else 0} rows", level="PENDING" if not p.exists() else "ERROR")
p2 = ROOT / "eval/T2_calendar.csv"
if p2.exists():
    calkeys = {(r["class_group"], r["module_name"], r["session"]) for r in cal}
    t2 = read(p2)
    bad = [r["id"] for r in t2 if r["class_group"] and r.get("expect_exists", "yes") == "yes" and (r["class_group"], r["module"], r["session"]) not in calkeys]
    check("T2 → D2: referenced (class, module, session) exist", not bad, str(bad))
p3 = ROOT / "eval/T3_contacts_requests.csv"
if p3.exists():
    bad = [r["id"] for r in read(p3) if r["expected_role_id"] not in roles]
    check("T3 → D3: expected_role_id exist", not bad, str(bad))
p4 = ROOT / "eval/T4_photos.csv"
if p4.exists():
    miss = [r["file"] for r in read(p4) if not (ROOT / "eval/T4_photos" / r["file"]).exists()]
    check("T4: every image file present", not miss, str(miss), level="PENDING")

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

# ---------------------------------------------------------------- report
for lvl, name, det in results:
    print(f"{lvl:7} {name}" + (f"  [{det}]" if det and lvl != "PASS" else ""))
err = sum(1 for r in results if r[0] == "ERROR")
pend = sum(1 for r in results if r[0] == "PENDING")
print(f"\n{len(results)} checks: {sum(1 for r in results if r[0] == 'PASS')} pass, {err} error, {pend} pending")
sys.exit(1 if err else 0)
