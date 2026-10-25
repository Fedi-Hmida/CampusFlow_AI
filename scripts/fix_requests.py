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
    "F_RI2": "D1-011/2/Accès aux locaux", "F_ABS4": "D1-004/4/Instruction de la demande",
    "F_REC4": "D1-008/4/Comment déposer la demande", "F_REC5": "D1-008/5/Traitement de la demande",
    "F_STG7": "D1-010/7/Dépôt et évaluation",
}
# Per-row decisions: regime, optional overrides, source_ref keys, evidence quote (doc, quote), note for the review
DECISIONS = {
    "REQ-01": dict(regime="all", src=["F_ATT4"], docs="Formulaire FORM-03 ; pièce d'identité (CIN, passeport ou carte d'étudiant)",
                   deadline="Aucun délai fixé", processing="3 jours ouvrables (délai indicatif)",
                   evidence=[("D1-006", "La demande se fait auprès du service de la scolarité avec le formulaire FORM-03 et une pièce d'identité"),
                             ("D1-006", "certificat de scolarité, 3 jours ouvrables")],
                   note="Two FICTITIOUS versions removed (Fedi): aligned with D1-006 art. 4 (delivered: e-mail + carte étudiant, 2–3 jours)."),
    "REQ-02": dict(regime="all", src=["F_ATT4"], docs="Formulaire FORM-03 ; pièce d'identité (CIN, passeport ou carte d'étudiant)",
                   deadline="Disponible à partir de la publication officielle des résultats",
                   processing="7 jours ouvrables à partir de la publication officielle des résultats (délai indicatif)",
                   evidence=[("D1-006", "relevé de notes, 7 jours ouvrables à partir de la publication officielle des résultats")],
                   note="Two FICTITIOUS versions removed: aligned with D1-006 art. 4 (delivered: e-mail, 3–5 jours, 5 jours avant la date d'utilisation)."),
    "REQ-03": dict(regime="all", src=[], note="No source."),
    "REQ-04": dict(regime="all", src=["F_RI2"], fict_detail="processing_time", deadline="Signaler la perte ou le vol à la scolarité dans un délai de 48 heures",
                   evidence=[("D1-011", "En cas de perte de la carte d'étudiant, l'étudiant le signale à la scolarité dans un délai de 48 heures.")],
                   note="Two FICTITIOUS versions removed: aligned with D1-011 art. 2 (delivered: 'dès la perte ou le vol')."),
    "REQ-05": dict(regime="all", src=[], note="No source."),
    "REQ-06": dict(regime="jour;soir", src=["J3", "S3"], fict_detail="processing_time", handler="SCO-GEN",
                   docs="Formulaire de demande de report rempli et déposé au bureau d'ordre de l'école",
                   deadline="Au plus tard le 30 novembre de l'année en cours (cours du jour : condition du remboursement ; cours du soir : aucune demande recevable après le 30 novembre) ; un seul report sur toute la scolarité",
                   evidence=[("D1-002", "Aucune demande de report d'inscription n'est recevable après le 30 novembre."),
                             ("D1-001", "Un formulaire de demande du report doit être rempli et déposé au bureau d’ordre de l’école.")],
                   note="CONFLICT fixed: delivered deadline 'avant le début du semestre' → official 30 November; official place = bureau d'ordre (handler set to SCO-GEN as the closest role)."),
    "REQ-07": "split",
    "REQ-08": "split",
    "REQ-09": dict(regime="all", src=["J78", "S72", "A8"], fict_detail="délai et organisation par le bureau des examens", note="Official: the scolarité (jour) or a commission (soir/alternance) decides the retake; the delivered deadline/organisation by EXA is FICTITIOUS."),
    "REQ-10": dict(regime="all", src=["J76", "S77"], fict_detail="délai d'inscription de 5 jours ouvrables", note="Official texts give the right to retake; the 5-day registration deadline is FICTITIOUS."),
    "REQ-11": dict(regime="all", src=["S72", "A72", "F_REC4", "F_REC5"],
                   docs="Demande écrite sur le formulaire FORM-02 (nom, prénom, classe, numéro d'étudiant, module, date de l'épreuve, note affichée, motif) ; pièce d'identité si demandée",
                   deadline="Cours du soir et alternance : une semaine après l'affichage de la note, auprès du service examen ; cours du jour : le règlement ne prévoit pas la double correction, l'étudiant se renseigne auprès du service examen",
                   processing="10 jours ouvrables après le dépôt de la demande (délai indicatif)",
                   evidence=[("D1-002", "dans un délai d’une semaine après l’affichage de la note de cette épreuve"),
                             ("D1-008", "Le formulaire à utiliser est le modèle FORM-02"),
                             ("D1-008", "Délai de traitement indicatif : 10 jours ouvrables après le dépôt de la demande."),
                             ("D1-008", "Le règlement du cours du jour ne la mentionne pas : l'étudiant du cours du jour se renseigne auprès du service examen.")],
                   note="CONFLICT fixed: delivered '3 jours ouvrables' contradicts the 1-week rule of soir/alternance; documents and processing time aligned with D1-008 (two FICTITIOUS versions removed)."),
    "REQ-12": dict(regime="all", src=[], note="No source."),
    "REQ-13": dict(regime="all", src=[], note="No source (the regulations describe discipline hearings, not a general appeal)."),
    "REQ-14": dict(regime="jour", src=["F_STG4"], fict_detail="required_documents, processing_time (D1-010 lists no documents)",
                   deadline="Convention tripartite signée par les trois parties avant le premier jour de stage et déposée au service des stages",
                   evidence=[("D1-010", "Avant le premier jour de stage, une convention de stage tripartite (étudiant, école, organisme d'accueil) est signée par les trois parties et déposée auprès du service des stages.")],
                   note="Two FICTITIOUS versions removed: aligned with D1-010 art. 4 (delivered: 'au moins 15 jours ouvrables avant le début du stage')."),
    "REQ-15": dict(regime="jour", src=["J79", "F_STG7"], fict_detail="processing_time", type="Dépôt de l'attestation et des livrables de stage",
                   docs="Attestation de stage délivrée par l'entreprise d'accueil ; journal et rapport de stage (à déposer au service des stages)",
                   deadline="Au plus tard le 30 septembre suivant la fin du stage",
                   evidence=[("D1-001", "une attestation de stage délivrée par l’entreprise d’accueil"),
                             ("D1-010", "sont déposés auprès du service des stages au plus tard le 30 septembre suivant la fin du stage.")],
                   note="CONFLICT fixed: the attestation is issued by the host company (official 7-9), not by the STAGE office; deadline aligned with D1-010 art. 7 (two FICTITIOUS versions removed)."),
    "REQ-16": dict(regime="all", src=[], note="No source."),
    "REQ-17": dict(regime="all", src=[], note="No source."), "REQ-18": dict(regime="all", src=[], note="No source."),
    "REQ-19": dict(regime="all", src=[], note="No source."), "REQ-20": dict(regime="all", src=[], note="No source."),
    "REQ-21": dict(regime="all", src=[], note="No source."), "REQ-22": dict(regime="all", src=[], note="No source."),
}
SPLITS = {
    "REQ-07": [
        dict(id="REQ-07-J", type="Justification d'absence en cours, TD ou TP (cours du jour)", regime="jour", src=["J9"], fict_detail="processing_time",
             docs="Justificatif d'absence (raison médicale ou force majeure) adressé au service de scolarité",
             deadline="Dans un délai maximal d'une semaine",
             evidence=[("D1-001", "un justificatif d’absence, dans un délai maximal d’une semaine.")],
             note="REQ-07 split by regime: one week for cours du jour (D1-001 art. 9) vs next day for soir/alternance (REQ-07-SA)."),
        dict(id="REQ-07-SA", type="Justification d'absence en cours, TD ou TP (cours du soir, alternance)", regime="soir;alternance",
             src=["S9", "A10"], fict_detail="processing_time", docs="Certificat médical ou justificatif adressé au service de scolarité",
             deadline="Au plus tard le lendemain du début de l'empêchement ; au-delà de trois absences non justifiées à un module : avertissement",
             evidence=[("D1-002", "l’élève doit adresser au Service de Scolarité un certificat médical ou un justificatif, au plus tard le lendemain du début de l’empêchement."),
                       ("D1-003", "l’élève doit adresser au Service de Scolarité un certificat médical ou un justificatif, au plus tard le lendemain du début de l’empêchement."),
                       ("D1-002", "Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève."),
                       ("D1-003", "Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève.")],
             note="One row for both regimes: D1-002 art. 9 and D1-003 art. 10 state the same rule (quotes above)."),
    ],
    "REQ-08": [
        dict(id="REQ-08-J", type="Justification d'absence à une épreuve finale (cours du jour)", regime="jour", src=["J78", "F_ABS3", "F_ABS4"],
             docs="Dossier de demande de repassage exceptionnel déposé à la scolarité ; justificatif recevable uniquement pour accident, maladie contagieuse, hospitalisation ou décès d'un parent proche (un certificat médical n'est pas un justificatif)",
             deadline="Aucun délai fixé par le règlement ; demande traitée au cas par cas",
             processing="7 jours ouvrables après le dépôt d'un dossier complet (délai indicatif)",
             evidence=[("D1-001", "Les certificats médicaux ne constituent pas un justificatif d’absence."),
                       ("D1-004", "Délai de réponse indicatif : 7 jours ouvrables après le dépôt d'un dossier complet.")],
             note="REQ-08 split by regime (official rules differ): cours du jour — certificate not accepted, no deadline; processing time from D1-004 art. 4 (FICTITIOUS)."),
        dict(id="REQ-08-SA", type="Justification d'absence à une épreuve (cours du soir, alternance)", regime="soir;alternance",
             src=["S72", "A8", "F_ABS4"], processing="7 jours ouvrables après le dépôt d'un dossier complet (délai indicatif)",
             docs="Pièces justificatives de force majeure (hospitalisation, décès d'un parent, mission de travail) ; un simple certificat médical n'est pas un motif valable (cours du soir) ou peut ne pas l'être (alternance)",
             deadline="Aviser le responsable de la scolarité dans un délai ne dépassant pas 48 h à compter de la date de l'épreuve",
             evidence=[("D1-002", "dans un délai ne dépassant pas 48h à compter de la date de l’épreuve"),
                       ("D1-003", "dans un délai ne dépassant pas 48h à compter de la date de l’épreuve"),
                       ("D1-004", "Délai de réponse indicatif : 7 jours ouvrables après le dépôt d'un dossier complet.")],
             note="REQ-08 split by regime: soir/alternance — force majeure, 48 h notice (D1-002 art. 7-2, D1-003 art. 8); processing time from D1-004 art. 4 (FICTITIOUS)."),
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
                       "Rule A2: where the delivered row contradicted an official article, the official rule was applied.", "",
                       "## Rows", ""]
    for r in raw:
        rid, dec = r["request_id"], DECISIONS[r["request_id"]]
        base = {c: r.get(c, "") for c in COLUMNS}
        variants = SPLITS[rid] if dec == "split" else [dict(id=rid, **dec)]
        for v in variants:
            row = dict(base, request_id=v["id"], regime=v["regime"], source_ref=ref(v["src"]),
                       request_type=v.get("type", base["request_type"]), handler_role_id=v.get("handler", base["handler_role_id"]),
                       required_documents=v.get("docs", base["required_documents"]),
                       deadline_rule=v.get("deadline", base["deadline_rule"]),
                       processing_time=v.get("processing", base["processing_time"]))
            off = sorted({K[k][:6] for k in v["src"] if K[k] < "D1-004"})
            fic = sorted({K[k][:6] for k in v["src"] if K[k] >= "D1-004"})
            changed = [c for c in ("request_type", "handler_role_id", "required_documents", "deadline_rule", "processing_time") if row[c] != base[c]]
            if not v["src"]:
                src = "FICTITIOUS — " + base["source"]
            else:
                src = (f"règlement officiel ({', '.join(off)})" if off else "FICTITIOUS") + \
                      (f" ; FICTITIOUS procedure ({', '.join(fic)})" if off and fic else (f" — procedure {', '.join(fic)}" if fic else "")) + \
                      (" ; values aligned with the cited articles (CF-108)" if changed else f" ; {base['source']}")
            if v.get("fict_detail"):
                src += f" ; FICTITIOUS (catalogue only): {v['fict_detail']}"
            row["source"] = src
            out.append(row)
            evs = v.get("evidence") or []
            review += [f"### {v['id']} — {row['request_type']} · regime `{row['regime']}` · handler `{row['handler_role_id']}`",
                       f"- source_ref: {row['source_ref']}", f"- source: {row['source']}"]
            for c in changed:
                review.append(f"- {c}: « {base[c]} » → « {row[c]} »")
            for d, quote in evs:
                loc = find_quote(d, quote)
                if not loc:
                    sys.exit(f"{v['id']}: evidence not found in {d}: {quote[:60]}")
                review.append(f"- evidence {d} · `{loc['key']}` · p.{loc['page']}: « {quote} »")
            review += [f"- note: {v.get('note', '')}",
                       "- [ ] OK  [ ] fix: ____", ""]
    with open(ROOT / "data/tables/request_catalogue.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows(out)
    write_review(ROOT / "eval/review/request_mapping_review.md", "\n".join(review) + "\n")
    print(f"request_catalogue.csv: {len(out)} rows ({len(raw)} delivered, REQ-07 and REQ-08 split by regime)")


if __name__ == "__main__":
    main()
