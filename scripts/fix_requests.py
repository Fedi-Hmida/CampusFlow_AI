"""CF-108 — request catalogue to spec D4 + regime (ADR-017, P5), aligned with the official regulations (A2).

Input : data/raw/tables/D4_catalogue_demandes.csv (untouched), data/regs/clean/ (for source_ref checks)
Output: data/tables/request_catalogue.csv, eval/review/request_mapping_review.md
source_ref = "<article key>" values separated by " | " (they must exist in data/regs/clean/), or
"FICTITIOUS — no source". Where the delivered value contradicts an official article, the official rule wins.
Run   : .venv/Scripts/python scripts/fix_requests.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from corpus_lookup import article_keys, find_quote, write_review  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["request_type", "handler_role_id", "required_documents", "deadline_rule", "source_ref", "regime",
           "request_id", "category", "routing_rule", "processing_time", "source"]
NO_SRC = "FICTITIOUS — no source"
K = {  # article keys used below (validated against the clean corpus)
    "J3": "D1-001/3/Inscription des élèves", "S3": "D1-002/3/Inscription des élèves",
    "J9": "D1-001/9/Assiduité", "S9": "D1-002/9/Assiduité", "A10": "D1-003/10/Assiduité",
    "J78": "D1-001/7-8/Déroulement des épreuves", "S72": "D1-002/7-2/Evaluation des élèves",
    "A72": "D1-003/7-2/Evaluation des alternant", "A8": "D1-003/8/Absences des examens",
    "J76": "D1-001/7-6/Session de rattrapage", "S77": "D1-002/7-7/Session de rattrapage",
    "J79": "D1-001/7-9/Stage", "F_ABS3": "D1-004/3/Dossier de demande de repassage exceptionnel",
    "F_ATT4": "D1-006/4/Comment faire la demande", "F_STG4": "D1-010/4/Recherche du stage et convention",
    "F_RI2": "D1-011/2/Accès aux locaux",
}
# Per-row decisions: regime, optional overrides, source_ref keys, evidence quote (doc, quote), note for the review
DECISIONS = {
    "REQ-01": dict(regime="all", src=["F_ATT4"], note="Only a FICTITIOUS source (D1-006 art. 4: FORM-03 + pièce d'identité, 3 jours ouvrables) — the delivered row says e-mail + carte étudiant, 2–3 jours: two fictitious versions, kept as delivered."),
    "REQ-02": dict(regime="all", src=["F_ATT4"], note="FICTITIOUS source only (D1-006: 7 jours ouvrables after publication)."),
    "REQ-03": dict(regime="all", src=[], note="No source."),
    "REQ-04": dict(regime="all", src=["F_RI2"], note="D1-011 art. 2 (FICTITIOUS) says report the loss within 48 h; delivered row says 'dès la perte'. Compatible, kept."),
    "REQ-05": dict(regime="all", src=[], note="No source."),
    "REQ-06": dict(regime="jour;soir", src=["J3", "S3"], handler="SCO-GEN",
                   docs="Formulaire de demande de report rempli et déposé au bureau d'ordre de l'école",
                   deadline="Au plus tard le 30 novembre de l'année en cours (cours du jour : condition du remboursement ; cours du soir : aucune demande recevable après le 30 novembre) ; un seul report sur toute la scolarité",
                   evidence=("D1-002", "Aucune demande de report d'inscription n'est recevable après le 30 novembre."),
                   note="CONFLICT fixed: delivered deadline 'avant le début du semestre' → official 30 November; official place = bureau d'ordre (handler set to SCO-GEN as the closest role)."),
    "REQ-07": "split",
    "REQ-08": "split",
    "REQ-09": dict(regime="all", src=["J78", "S72", "A8"], fict_detail="délai et organisation par le bureau des examens", note="Official: the scolarité (jour) or a commission (soir/alternance) decides the retake; the delivered deadline/organisation by EXA is FICTITIOUS."),
    "REQ-10": dict(regime="all", src=["J76", "S77"], fict_detail="délai d'inscription de 5 jours ouvrables", note="Official texts give the right to retake; the 5-day registration deadline is FICTITIOUS."),
    "REQ-11": dict(regime="all", src=["S72", "A72"],
                   deadline="Cours du soir et alternance : une semaine après l'affichage de la note (demande de double correction auprès du service examen) ; cours du jour : non fixé par le règlement (FICTITIOUS : 3 jours ouvrables après la publication des résultats)",
                   evidence=("D1-002", "dans un délai d’une semaine après l’affichage de la note de cette épreuve"),
                   note="CONFLICT fixed: delivered '3 jours ouvrables' contradicts the 1-week rule of soir/alternance."),
    "REQ-12": dict(regime="all", src=[], note="No source."),
    "REQ-13": dict(regime="all", src=[], note="No source (the regulations describe discipline hearings, not a general appeal)."),
    "REQ-14": dict(regime="jour", src=["F_STG4"], note="FICTITIOUS sources only (D1-010: convention signed before the first day)."),
    "REQ-15": dict(regime="jour", src=["J79"], type="Dépôt de l'attestation et des livrables de stage",
                   docs="Attestation de stage délivrée par l'entreprise d'accueil ; journal et rapport de stage (à déposer au service des stages)",
                   evidence=("D1-001", "une attestation de stage délivrée par l’entreprise d’accueil"),
                   note="CONFLICT fixed: the attestation is issued by the host company (official 7-9), not by the STAGE office; the request becomes 'dépôt' of the deliverables."),
    "REQ-16": dict(regime="all", src=[], note="No source."),
    "REQ-17": dict(regime="all", src=[], note="No source."), "REQ-18": dict(regime="all", src=[], note="No source."),
    "REQ-19": dict(regime="all", src=[], note="No source."), "REQ-20": dict(regime="all", src=[], note="No source."),
    "REQ-21": dict(regime="all", src=[], note="No source."), "REQ-22": dict(regime="all", src=[], note="No source."),
}
SPLITS = {
    "REQ-07": [
        dict(id="REQ-07-J", type="Justification d'absence en cours, TD ou TP (cours du jour)", regime="jour", src=["J9"],
             docs="Justificatif d'absence (raison médicale ou force majeure) adressé au service de scolarité",
             deadline="Dans un délai maximal d'une semaine",
             evidence=("D1-001", "un justificatif d’absence, dans un délai maximal d’une semaine.")),
        dict(id="REQ-07-SA", type="Justification d'absence en cours, TD ou TP (cours du soir, alternance)", regime="soir;alternance",
             src=["S9", "A10"], docs="Certificat médical ou justificatif adressé au service de scolarité",
             deadline="Au plus tard le lendemain du début de l'empêchement ; au-delà de trois absences non justifiées à un module : avertissement",
             evidence=("D1-002", "au plus tard le lendemain du début de l’empêchement.")),
    ],
    "REQ-08": [
        dict(id="REQ-08-J", type="Justification d'absence à une épreuve finale (cours du jour)", regime="jour", src=["J78", "F_ABS3"],
             docs="Dossier de demande de repassage exceptionnel déposé à la scolarité ; justificatif recevable uniquement pour accident, maladie contagieuse, hospitalisation ou décès d'un parent proche (un certificat médical n'est pas un justificatif)",
             deadline="Aucun délai fixé par le règlement ; demande traitée au cas par cas",
             evidence=("D1-001", "Les certificats médicaux ne constituent pas un justificatif d’absence.")),
        dict(id="REQ-08-SA", type="Justification d'absence à une épreuve (cours du soir, alternance)", regime="soir;alternance",
             src=["S72", "A8"],
             docs="Pièces justificatives de force majeure (hospitalisation, décès d'un parent, mission de travail) ; un simple certificat médical n'est pas un motif valable (cours du soir) ou peut ne pas l'être (alternance)",
             deadline="Aviser le responsable de la scolarité dans un délai ne dépassant pas 48 h à compter de la date de l'épreuve",
             evidence=("D1-002", "dans un délai ne dépassant pas 48h à compter de la date de l’épreuve")),
    ],
}


def ref(keys: list[str]) -> str:
    return " | ".join(K[k] for k in keys) if keys else NO_SRC


def main() -> None:
    known = article_keys()
    bad = [v for v in K.values() if v not in known]
    if bad:
        sys.exit(f"unknown article keys: {bad}")
    raw = list(csv.DictReader(open(ROOT / "data/raw/tables/D4_catalogue_demandes.csv", encoding="utf-8")))
    out, review = [], ["# CF-108 — Request catalogue mapping review", "",
                       "Each row: delivered value → catalogue value, the article keys it now cites and the evidence. Tick or fix.",
                       "Rule A2: where the delivered row contradicted an official article, the official rule was applied.", ""]
    for r in raw:
        rid, dec = r["request_id"], DECISIONS[r["request_id"]]
        base = {c: r.get(c, "") for c in COLUMNS}
        variants = SPLITS[rid] if dec == "split" else [dict(id=rid, **dec)]
        for v in variants:
            row = dict(base, request_id=v["id"], regime=v["regime"], source_ref=ref(v["src"]),
                       request_type=v.get("type", base["request_type"]), handler_role_id=v.get("handler", base["handler_role_id"]),
                       required_documents=v.get("docs", base["required_documents"]),
                       deadline_rule=v.get("deadline", base["deadline_rule"]))
            fict = (not v["src"]) or all(K[k].split("/")[0] >= "D1-004" for k in v["src"])
            changed = [c for c in ("request_type", "handler_role_id", "required_documents", "deadline_rule") if row[c] != base[c]]
            row["source"] = ("FICTITIOUS — " if fict else "règlement officiel (" + ", ".join(sorted({K[k][:6] for k in v['src'] if K[k] < 'D1-004'})) + ") ; ") + \
                ("values aligned with the official article (CF-108)" if changed else base["source"])
            if v.get("fict_detail"):
                row["source"] += f" ; FICTITIOUS: {v['fict_detail']}"
            if rid == "REQ-04" or fict and "FICTITIOUS" not in row["source"]:
                row["source"] = "FICTITIOUS — " + base["source"]
            out.append(row)
            ev = v.get("evidence")
            loc = find_quote(*ev) if ev else None
            if ev and not loc:
                sys.exit(f"{v['id']}: evidence not found")
            review += [f"### {v['id']} — {row['request_type']} · regime `{row['regime']}` · handler `{row['handler_role_id']}`",
                       f"- source_ref: {row['source_ref']}"]
            for c in changed:
                review.append(f"- {c}: « {base[c]} » → « {row[c]} »")
            if ev:
                review.append(f"- evidence {ev[0]} · `{loc['key']}` · p.{loc['page']}: « {ev[1]} »")
            review += [f"- note: {v.get('note') or DECISIONS[rid] if dec != 'split' else 'Split by regime (official rules differ).'}",
                       "- [ ] OK  [ ] fix: ____", ""]
    with open(ROOT / "data/tables/request_catalogue.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows(out)
    write_review(ROOT / "eval/review/request_mapping_review.md", "\n".join(review) + "\n")
    print(f"request_catalogue.csv: {len(out)} rows ({len(raw)} delivered, REQ-07 and REQ-08 split by regime)")


if __name__ == "__main__":
    main()
