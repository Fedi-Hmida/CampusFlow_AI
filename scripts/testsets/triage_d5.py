"""CF-208b — triage Doua's synthetic question file D5 against the approved data.

  in : eval/candidates/D5_original_2026-10-25.csv  (Doua's delivery, kept verbatim)
  out: eval/candidates/D5_triage.csv                (one row per question: new D5- id, status, reasons, Router dev labels)

D5 is NOT a test set: its answers cite a second dataset that was never imported (data/INTAKE.md). What stays usable
without that dataset is the routing label of each question → `router_dev = yes` rows form a Router development set.
Statuses (first match wins):
  leak            question shares >= 6 consecutive words with an official T1–T5 question
  rule_conflict   the expected answer contradicts approved data (manual rulings below, each with its evidence key)
  blocked_source  the expected answer cites a source absent from data/regs/clean, data/tables or the catalogue
  route_only      no source-dependent fact to check (refusal, injection, out of scope)
  supported       every cited source exists and the answer's numbers appear in it
Run: .venv/Scripts/python scripts/testsets/triage_d5.py
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from corpus_lookup import article_keys, canon, doc, longest_shared_run  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "eval/candidates/D5_original_2026-10-25.csv"
OUT = ROOT / "eval/candidates/D5_triage.csv"
COLS = ["d5_id", "original_id", "language", "level", "regime_in_question", "has_photo", "question", "router_intents",
        "status", "reasons", "router_dev"]

# Manual rulings — only where a contradiction needs reading, never a guess. Evidence = approved article key / table row.
CONFLICTS = {
    "T1-13": "regime-blind: for cours du jour a medical certificate is not a valid justification (D1-001/7-8/Déroulement des épreuves)",
    "T1-EN-01": "regime-blind: for cours du jour a medical certificate is not a valid justification (D1-001/7-8/Déroulement des épreuves)",
    "MIX-01": "regime-blind: for cours du jour a medical certificate is not a valid justification (D1-001/7-8/Déroulement des épreuves)",
    "T3-04": "uses the old '3 jours ouvrables' delay; approved REQ-08-J (jour) has no fixed delay, REQ-08-SA (soir;alternance) 48 h",
}
# D5 route labels → Router intents (regulations | calendar | admin | vision | out_of_scope). `not_found` is an answer,
# not a route: those rows are routed to the domain a student would expect, read from the question.
NOT_FOUND_ROUTE = {"T5-05": "admin", "T5-06": "calendar", "T5-08": "vision;calendar"}
REGIME_WORDS = {"jour": r"cours du jour|\bjour\b", "soir": r"cours du soir|\bsoir\b", "alternance": r"alternance"}


def read(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig", newline="") as f:     # utf-8-sig: the delivery carries a BOM
        return list(csv.DictReader(f))


def official_questions() -> list[tuple[str, str]]:
    out = []
    for name in ("T1_regulations", "T2_calendar", "T3_contacts_requests", "T5_adversarial"):
        out += [(r["id"], r.get("question") or r["question_or_input"]) for r in read(ROOT / f"eval/testsets/{name}.csv")]
    return out


def numbers(s: str) -> set[str]:
    """Numeric facts of an answer: '10/20', '8', '30 %', '5 jours' → {'10/20', '8', '30', '5'}."""
    return set(re.findall(r"\d+(?:/\d+)?", s))


def content_words(s: str) -> set[str]:
    """Words of >= 6 letters (accents folded): the claim-bearing vocabulary of an answer."""
    folded = unicodedata.normalize("NFKD", canon(s)).encode("ascii", "ignore").decode()
    return set(re.findall(r"[a-z]{6,}", folded))


def evidence(src: str, contact: str, answer: str, roles: dict, reqs: dict) -> tuple[str, list[str]]:
    """Text of every cited source that exists in the approved data, and the reasons for each missing or
    off-topic source. Each cited article must on its own cover >= 30 % of the answer's content words, so a
    wrong article number cannot hide behind the other sources of the same row."""
    pool, reasons = [], []
    words = content_words(answer)
    for d, art in re.findall(r"(D1-\d{3}) art\.(\d+)", src):
        keys = sorted(k for k in article_keys(d) if k.split("/")[1] == art)   # sorted: D1-003 has two articles 12
        if not keys:
            reasons.append(f"{d} has no article {art} in data/regs/clean")
            continue
        text = " ".join(u["text"] for u in doc(d)["articles"] if u["key"] in keys)
        if words and len(words & content_words(text)) / len(words) < 0.3:
            reasons.append(f"{d} art.{art} is {' / '.join(repr(k.split('/')[2]) for k in keys)} in the approved corpus — off-topic for this answer")
        pool.append(text)
    for d in re.findall(r"(D1-\d{3}) p\.\d+", src):
        reasons.append(f"{d} cited by page only: the approved {d} is '{doc(d)['title']}' — different document (second dataset)")
    for ex in re.findall(r"EX-[\w-]+", src):
        reasons.append(f"calendar row {ex} not in data/tables/exam_calendar.csv (no such id; rooms/times not in the table)")
    if "périodes officielles" in src:
        reasons.append("academic periods table not in data/tables (second dataset)")
    for req in re.findall(r"REQ-\d+", src):
        rows = [r for rid, r in reqs.items() if rid == req or rid.startswith(req + "-")]
        if not rows:
            reasons.append(f"{req} not in data/tables/request_catalogue.csv")
        pool += [" ".join(r.values()) for r in rows]
    for rid in re.findall(r"\b(SCO-\w+|[A-Z]{2,}(?:-[A-Z]+)?)\b", src.split("D3", 1)[1] if "D3" in src else ""):
        if rid in roles:
            pool.append(" ".join(roles[rid].values()))
        elif not rid.startswith(("REQ", "D", "EXA", "SCO-GEN")) or rid in ("DEP-HEAD", "DIR-ETU", "DIR"):
            reasons.append(f"role {rid} not in data/tables/directory.csv")
    emails = {r["email"] for r in roles.values()}
    for e in re.findall(r"[\w.+-]+@[\w.-]+", contact):
        if e not in emails:
            reasons.append(f"contact {e} not in data/tables/directory.csv")
    return " ".join(pool), reasons


def claim_reasons(answer: str, pool: str) -> list[str]:
    """Every number and >= 60 % of the content words of the answer must appear in the cited evidence."""
    out = []
    miss = sorted(n for n in numbers(answer) if n not in numbers(pool))
    if miss:
        out.append(f"numbers {miss} not in the cited evidence")
    words = content_words(answer)
    if words:
        cover = len(words & content_words(pool)) / len(words)
        if cover < 0.6:
            out.append(f"only {cover:.0%} of the answer's content words appear in the cited evidence")
    return out


def intents(r: dict) -> str:
    if r["id"] in NOT_FOUND_ROUTE:
        return NOT_FOUND_ROUTE[r["id"]]
    return r["expected_route"].replace("+", ";")


def main() -> None:
    rows = read(SRC)
    roles = {r["role_id"]: r for r in read(ROOT / "data/tables/directory.csv")}
    reqs = {r["request_id"]: r for r in read(ROOT / "data/tables/request_catalogue.csv")}
    official = official_questions()
    out = []
    for i, r in enumerate(rows, 1):
        q, src, ans = r["question"], r["expected_source"], r["expected_answer"]
        leak = max(((longest_shared_run(q, oq), oid) for oid, oq in official), default=(0, ""))
        pool, reasons = evidence(src, r["expected_contact"], ans, roles, reqs)
        if r["expected_route"] == "out_of_scope" or not src.strip():
            claims = []                     # refusals: the answer describes behaviour, not facts from a source
        else:
            claims = claim_reasons(ans, pool)
        if leak[0] >= 6:
            status, why = "leak", [f"shares {leak[0]} consecutive words with {leak[1]}"] + reasons
        elif r["id"] in CONFLICTS:
            status, why = "rule_conflict", [CONFLICTS[r["id"]]] + reasons
        elif reasons or claims:
            status, why = "blocked_source", reasons + claims
        elif r["expected_route"] == "out_of_scope" or not src.strip():
            status, why = "route_only", ["no source-dependent fact" if not src.strip() else "refusal; cited rule only as context"]
        else:
            status, why = "supported", []
        found = [reg for reg, pat in REGIME_WORDS.items() if re.search(pat, q, re.I)]
        out.append({
            "d5_id": f"D5-{i:03d}", "original_id": r["id"], "language": r["language"].lower(), "level": r["level"],
            "regime_in_question": ";".join(found), "has_photo": "yes" if q.startswith("[Photo") else "no",
            "question": q, "router_intents": intents(r), "status": status, "reasons": " | ".join(why),
            "router_dev": "no" if status == "leak" else "yes",
        })
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    counts = {}
    for o in out:
        counts[o["status"]] = counts.get(o["status"], 0) + 1
    print(f"{OUT.relative_to(ROOT).as_posix()}: {len(out)} rows {counts}; router_dev yes = {sum(o['router_dev'] == 'yes' for o in out)}")


if __name__ == "__main__":
    main()
