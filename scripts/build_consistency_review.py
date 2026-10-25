"""CF-108b — build eval/review/consistency_review.md (FICTITIOUS procedures vs official regulations).

Every quote (fictitious and official) is located verbatim in data/regs/clean/; the script stops if one is missing.
Run: .venv/Scripts/python scripts/build_consistency_review.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from corpus_lookup import canon, doc, find_quote  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CORR = json.loads((ROOT / "scripts/fictif_corrections.json").read_text(encoding="utf-8"))

# Overlaps checked and found consistent: (topic, fictitious doc, fictitious quote, official doc, official quote)
CONSISTENT = [
    ("absences (day)", "D1-004", "Cours du jour : seuls les cas d'accident, de maladie contagieuse, d'hospitalisation ou de décès d'un parent",
     "D1-001", "Seuls les cas d’accidents, de maladies contagieuses, d’hospitalisations où de décès d’un parent proche"),
    ("absences (evening/work-study)", "D1-004", "dans un délai ne dépassant pas 48 heures à compter",
     "D1-002", "dans un délai ne dépassant pas 48h à compter de la date de l’épreuve"),
    ("assiduity", "D1-004", "le justificatif est adressé au service de scolarité dans un délai maximal d'une semaine",
     "D1-001", "un justificatif d’absence, dans un délai maximal d’une semaine"),
    ("assiduity (evening/work-study)", "D1-004", "au plus tard le lendemain du début de l'empêchement",
     "D1-002", "au plus tard le lendemain du début de l’empêchement"),
    ("retakes (day)", "D1-004", "Les projets intégrés ne sont pas rattrapables",
     "D1-001", "Les projets intégrés ne sont pas rattrapables"),
    ("retakes (evening)", "D1-004", "la note de l'examen de rattrapage est écrêtée à 10/20",
     "D1-002", "la note obtenue à l’examen de rattrapage est écrêtée à 10/20"),
    ("retakes (work-study)", "D1-004", "Un projet (autre que le PFE) peut être validé, refusé ou",
     "D1-003", "Un projet (autre que le PFE) peut être validé, refusé ou faire l'objet d'un rattrapage"),
    ("PFE (day)", "D1-007", "un rapport anti-plagiat avec un taux de plagiat inférieur à 18 %",
     "D1-001", "Un rapport anti-plagiat avec un taux de plagiat inférieur à 18%"),
    ("PFE (evening)", "D1-007", "Cours du soir : durée minimale de 5 mois, à réaliser en entreprise, en 4ème année.",
     "D1-002", "d'une durée minimale de 5 mois, peut démarrer pour un étudiant inscrit"),
    ("PFE (work-study)", "D1-007", "seuls les élèves ayant réussi les examens de la 4ème année et validé",
     "D1-003", "Ne sont autorisés à soutenir le projet de fin d’études que les élèves ayant réussi les examens de la quatrième année"),
    ("PFE jury (evening/work-study)", "D1-007", "le jury est désigné par le directeur de l'école et compte au moins trois membres",
     "D1-002", "Ce jury est composé au moins de trois membres dont le président du jury, le ou les encadrants et le rapporteur."),
    ("registration", "D1-009", "Chaque étudiant bénéficie d'un seul report sur la durée totale de sa scolarité.",
     "D1-001", "Chaque étudiant bénéficie d’un seul report d’inscription sur la durée totale de la scolarité."),
    ("registration (refund, evening)", "D1-009", "le remboursement est effectué dans un délai ne dépassant pas un mois",
     "D1-002", "remboursable dans un délai ne dépassant pas un mois à compter de la date de notification"),
    ("repeating a year", "D1-009", "une seule fois au cours des quatre années (cours du soir et alternance)",
     "D1-002", "Le redoublement est autorisé une seule fois au cours des quatre années de la scolarité."),
    ("internships", "D1-010", "Stage ingénieur : 5 ECTS, 8 semaines minimum",
     "D1-001", "Stage: Stage ingénieur; Nombre d'ECTS: 5; Durée minimale: 8 semaines"),
    ("exam room rules", "D1-005", "Aucun étudiant ne peut quitter la salle avant 30 minutes.",
     "D1-001", "L’étudiant pourra quitter la salle après au moins 30 minutes du démarrage de l’épreuve."),
]
# FICTITIOUS details with no official counterpart (kept, labelled FICTIF; never cited as official)
ADDITIONS = [
    ("D1-004", "Délai de réponse indicatif : 7 jours ouvrables après le dépôt d'un dossier complet."),
    ("D1-005", "un temps supplémentaire d'un tiers de la durée de l'épreuve"),
    ("D1-005", "Il est déposé à la scolarité au moins 7 jours avant le début de la session d'examens."),
    ("D1-006", "certificat de scolarité, 3 jours ouvrables ; relevé de notes, 7 jours ouvrables"),
    ("D1-007", "Le rapport complet est déposé au plus tard 15 jours avant la date de soutenance."),
    ("D1-008", "Si l'écart entre les deux notes dépasse 3 points sur"),
    ("D1-010", "au plus tard le 30 septembre suivant la fin du stage"),
    ("D1-010", "un taux de similarité inférieur à 18 % est attendu, comme pour le"),
    ("D1-011", "l'étudiant le signale à la scolarité dans un délai de 48 heures"),
]


def loc(doc_id: str, quote: str) -> str:
    f = find_quote(doc_id, quote)
    if not f:
        sys.exit(f"QUOTE NOT FOUND in {doc_id}: {quote[:80]}")
    return f"{doc_id} · `{f['key']}` · p.{f['page']}"


def main() -> None:
    out = ["# CF-108b — Consistency review: FICTITIOUS procedures vs official regulations", "",
           "Generated by `scripts/build_consistency_review.py`; every quote below was found verbatim in `data/regs/clean/`.",
           "Precedence rule (A2): when they disagree, **the official regulation wins**; the fictitious text is corrected",
           "before regeneration (CF-104). Tick each correction.", "",
           f"## 1. Conflicts and corrections ({sum(c['type'] == 'conflict' for c in CORR)} conflicts, "
           f"{sum(c['type'] != 'conflict' for c in CORR)} clarification)", ""]
    for c in CORR:
        out += [f"### {c['id']} — {c['topic']} ({c['type']})",
                f"- **Fictitious** ({loc(c['doc_id'], c['old'])}): « {c['old']} »"]
        for o in c["official"]:
            out.append(f"- **Official** ({loc(o['doc_id'], o['quote'])}): « {o['quote']} »")
        if c.get("official_absent"):
            a = c["official_absent"]
            hits = canon(" ".join(p["text"] for p in doc(a["doc_id"])["pages"])).count(canon(a["search"]))
            out.append(f"- **Official absent**: « {a['search']} » appears {hits} time(s) in {a['doc_id']}.")
        out += [f"- **Why**: {c['reason']}", f"- **Proposed text**: « {c['new']} »", "- [ ] OK  [ ] fix: ____", ""]
    out += ["## 2. Overlaps checked and consistent", "", "| Topic | Fictitious | Official |", "|---|---|---|"]
    for t, fd, fq, od, oq in CONSISTENT:
        out.append(f"| {t} | {loc(fd, fq)}: « {fq} » | {loc(od, oq)}: « {oq} » |")
    out += ["", "## 3. FICTITIOUS-only details (no official counterpart — kept, labelled, never cited as official)", "",
            "| Location | Text |", "|---|---|"]
    for d, q in ADDITIONS:
        out.append(f"| {loc(d, q)} | « {q} » |")
    out += ["", "## 4. Regime of the fictitious documents (A3)", "",
            "- D1-007 (PFE) contains rules for **jour, soir and alternance** (art. 2 and 5) → regime set to `all` "
            "(the plan said `jour;soir`).", "- D1-009 (report/annulation) covers jour and soir only → `jour;soir`.",
            "- D1-010 (stages) covers the 3 day-course internships → `jour`.", "- D1-004, D1-005, D1-006, D1-008, D1-011 → `all`."]
    p = ROOT / "eval/review/consistency_review.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"written {p.relative_to(ROOT)}: {len(CORR)} corrections, {len(CONSISTENT)} consistent overlaps, {len(ADDITIONS)} additions")


if __name__ == "__main__":
    main()
