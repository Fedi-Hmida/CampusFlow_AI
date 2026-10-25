"""CF-106 — transform the delivered exam calendar to the spec D2 schema (ADR-016, P1, P2, A7).

Input : data/raw/tables/exam_calendar_D2_v4.xlsx (untouched)
Output: data/tables/exam_calendar.csv, data/tables/module_codes.csv
Rules : unknown values stay EMPTY (end_time and room of the projected rows); the FICTITIOUS demo block is the only
        place with rooms and end times; every row carries data_status and last_updated.
Run   : .venv/Scripts/python scripts/tables/transform_calendar.py
"""
import csv
import re
import unicodedata
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/tables/exam_calendar_D2_v4.xlsx"
OUT = ROOT / "data/tables"
LAST_UPDATED = "2026-10-25"
PROJECTED = "projected from 2025-2026"
FICT = "FICTITIOUS"

COLUMNS = ["exam_id", "module_code", "module_name", "module_name_norm", "class_group", "semester", "session",
           "exam_type", "assessment", "date", "start_time", "end_time", "room", "last_updated", "data_status"]
SESSION = {"S1P1": ("S1", "Principale"), "S2P1": ("S2", "Principale")}
EXAM_TYPE = {"Ecrit": "Written", "Pratique": "Practical", "Soutenance": "Project defence", "Certification": "Certification"}
ASSESSMENT = {"EX": "Examen", "DS": "DS"}

DEMO_MODULES = {"DS14": "Advanced Deep Learning", "DS12": "Big Data Analytics", "DS15": "MLOps et déploiement"}
DEMO_CLASSES = {"5DS6": "B12", "5DS7": "B13", "5SIM1": "C04"}  # room for the Principale session
DEMO_SLOTS = [  # module, session, date, start, end, room (None = class room above)
    ("DS14", "Principale", "2027-01-15", "09:00", "11:00", None),
    ("DS12", "Principale", "2027-01-18", "13:00", "15:00", None),
    ("DS15", "Principale", "2027-01-20", "09:00", "11:00", None),
    ("DS14", "Rattrapage", "2027-02-15", "09:00", "11:00", "A21"),
    ("DS12", "Rattrapage", "2027-02-16", "09:00", "11:00", "A21"),
    ("DS15", "Rattrapage", "2027-02-17", "09:00", "11:00", "A21"),
]


def norm(s: str) -> str:
    """Lowercase, accents and punctuation removed, spaces collapsed (A7)."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


def main() -> None:
    ws = openpyxl.load_workbook(RAW, read_only=True, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    head, raw = rows[0], [dict(zip(rows[0], r)) for r in rows[1:]]
    names = sorted({r["module"].strip() for r in raw}, key=str.casefold)
    code = {n: f"M{i:03d}" for i, n in enumerate(names, 1)}
    out, cleaned_classes = [], set()
    for r in raw:
        cls = re.sub(r"\s+", "", r["class_group"])
        if cls != r["class_group"]:
            cleaned_classes.add(r["class_group"])
        sem, sess = SESSION[r["session"]]
        name = r["module"].strip()
        out.append({"exam_id": r["exam_id"], "module_code": code[name], "module_name": name, "module_name_norm": norm(name),
                    "class_group": cls, "semester": sem, "session": sess, "exam_type": EXAM_TYPE[r["exam_format"]],
                    "assessment": ASSESSMENT[r["exam_type"]], "date": r["date"].strftime("%Y-%m-%d"),
                    "start_time": r["time"].strftime("%H:%M"), "end_time": "", "room": "",
                    "last_updated": LAST_UPDATED, "data_status": PROJECTED})
    n = 0
    for mod, sess, date, start, end, room in DEMO_SLOTS:
        for cls, class_room in DEMO_CLASSES.items():
            n += 1
            out.append({"exam_id": f"FX{n:03d}", "module_code": mod, "module_name": DEMO_MODULES[mod],
                        "module_name_norm": norm(DEMO_MODULES[mod]), "class_group": cls, "semester": "S1", "session": sess,
                        "exam_type": "Written", "assessment": "Examen", "date": date, "start_time": start, "end_time": end,
                        "room": room or class_room, "last_updated": LAST_UPDATED, "data_status": FICT})
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "exam_calendar.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows(out)
    with open(OUT / "module_codes.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["module_code", "module_name", "module_name_norm", "data_status"])
        w.writerows([code[nm], nm, norm(nm), "generated code (official module name)"] for nm in names)
        w.writerows([c, nm, norm(nm), FICT] for c, nm in DEMO_MODULES.items())
    print(f"exam_calendar.csv: {len(out)} rows ({len(raw)} projected + {n} FICTITIOUS); module_codes.csv: {len(names) + len(DEMO_MODULES)} rows")
    print(f"class_group whitespace cleaned: {sorted(cleaned_classes)[:3]}… ({len(cleaned_classes)} values)")


if __name__ == "__main__":
    main()
