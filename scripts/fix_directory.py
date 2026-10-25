"""CF-107 — directory to the spec D3 schema (+ level_scope, source), missing roles added as FICTITIOUS (P3, P5).

Input : data/raw/tables/D3_annuaire_hierarchie.csv (untouched)
Output: data/tables/directory.csv
Invented roles use the reserved domain esprit.example (RFC 2606) and leave office/hours EMPTY (unknown).
Run   : .venv/Scripts/python scripts/fix_directory.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["role_id", "role_title", "department", "person_name", "email", "office", "hours", "handles", "reports_to",
           "escalation_level", "level_scope", "source"]
DEPARTMENT = {"SCO-1A": "Scolarité", "SCO-2A": "Scolarité", "SCO-3A": "Scolarité", "SCO-4A": "Scolarité",
              "SCO-5A": "Scolarité", "SCO-GEN": "Scolarité", "EXA": "Examens", "STAGE": "Stages",
              "MOB": "Relations internationales", "FIN": "Finance", "CAREER": "Carrières", "DEP-HEAD": "Départements",
              "DIR-ETU": "Direction des études", "DIR": "Direction générale"}
NEW_ROLES = [
    {"role_id": "COORD-DS", "role_title": "Coordinateur de programme — Data Science", "department": "Départements",
     "email": "coordination.ds@esprit.example", "handles": "Suivi pédagogique de la filière Data Science : options, emplois du temps, projets intégrés",
     "reports_to": "DEP-HEAD", "escalation_level": "1", "level_scope": "DS (4e et 5e année)"},
    {"role_id": "COORD-INFO", "role_title": "Coordinateur de programme — Informatique", "department": "Départements",
     "email": "coordination.info@esprit.example", "handles": "Suivi pédagogique des filières informatiques : options, emplois du temps, projets intégrés",
     "reports_to": "DEP-HEAD", "escalation_level": "1", "level_scope": "filières informatiques (3e à 5e année)"},
    {"role_id": "VIE-ETU", "role_title": "Vie étudiante", "department": "Vie étudiante",
     "email": "vie.etudiante@esprit.example", "handles": "Clubs et activités, orientation vers la cellule d'écoute et d'accompagnement",
     "reports_to": "DIR-ETU", "escalation_level": "1", "level_scope": "tous niveaux"},
    {"role_id": "IT-SUP", "role_title": "Support informatique", "department": "Systèmes d'information",
     "email": "support.it@esprit.example", "handles": "Comptes étudiants, espace étudiant et plateformes pédagogiques, accès réseau",
     "reports_to": "DIR", "escalation_level": "1", "level_scope": "tous niveaux"},
]


def main() -> None:
    raw = list(csv.DictReader(open(ROOT / "data/raw/tables/D3_annuaire_hierarchie.csv", encoding="utf-8")))
    out = []
    for r in raw:
        src = r["source"].strip()
        if "confirmer" in src:
            src += " ; FICTITIOUS (office/hours not verified)"
        out.append({**{c: r.get(c, "") for c in COLUMNS}, "department": DEPARTMENT[r["role_id"]], "person_name": "", "source": src})
    for n in NEW_ROLES:
        out.append({**{c: "" for c in COLUMNS}, **n, "source": "FICTITIOUS — invented role (CF-107); office and hours unknown"})
    with open(ROOT / "data/tables/directory.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows(out)
    print(f"directory.csv: {len(out)} roles ({len(raw)} delivered + {len(NEW_ROLES)} FICTITIOUS)")


if __name__ == "__main__":
    main()
