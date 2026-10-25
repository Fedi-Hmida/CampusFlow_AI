"""CF-111 — build the T1 regulation test set and its review sheet.

The expected article key and page are NOT typed by hand: they are derived from the supporting quotes, located
verbatim in data/regs/clean/ (A4). The script also enforces the A5 rule (a question may not reuse more than 5
consecutive words of its source article) and the coverage rules of the plan (§3.6).
Outputs: eval/T1_regulations.csv (verified_by stays empty until Fedi ticks the row) and eval/review/T1_review.md.
Run: .venv/Scripts/python scripts/build_t1.py
"""
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from corpus_lookup import all_doc_ids, canon, doc, find_quote, longest_shared_run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "eval/review/T1_verified.json"  # {"T1-01": "Fedi", ...} written after Fedi's review

# id, question (student wording, typos intended), regime, topic, [(doc_id, quote)], expected answer, pair group
ROWS = [
    ("T1-01", "Jsuis tombé malade le jour de mon exam final (grosse migraine), j'ai un certif du médecin : ça suffit pour le repasser ?",
     "jour", "absences", [("D1-001", "Les certificats médicaux ne constituent pas un justificatif d’absence."),
                          ("D1-001", "Toutefois, les demandes de repassage exceptionnelles sont traitées au cas par cas")],
     "Non. En cours du jour, seuls un accident, une maladie contagieuse, une hospitalisation ou le décès d'un parent proche justifient une absence à une épreuve finale ; un certificat médical ne suffit pas. L'étudiant peut déposer un dossier de repassage exceptionnel à la scolarité, traité au cas par cas.", "P-absence"),
    ("T1-02", "Cours du soir : j'ai loupé l'examen à cause d'une migraine et j'ai seulement un certificat médical, est-ce que ça marche ?",
     "soir", "absences", [("D1-002", "Il est à noter qu’un simple certificat médical n'est pas considéré comme un motif valable."),
                          ("D1-002", "dans un délai ne dépassant pas 48h à compter de la date de l’épreuve")],
     "Non, un simple certificat médical n'est pas un motif valable. En cas de force majeure (hospitalisation, décès d'un parent, mission de travail), il faut aviser le responsable de la scolarité dans les 48 h suivant l'épreuve avec les justificatifs ; une commission accorde ou refuse le repassage.", "P-absence"),
    ("T1-03", "Je suis en alternance et j'étais malade le jour d'un examen, j'ai qu'un certificat du médecin. Je fais comment ?",
     "alternance", "absences", [("D1-003", "dans un délai ne dépassant pas 48h à compter de la date de l’épreuve avec remise des pièces justificatives"),
                                ("D1-003", "un simple certificat médical peut ne pas être considéré comme un motif valable")],
     "Aviser le responsable de la scolarité dans les 48 h suivant l'épreuve, avec les pièces justificatives. Un simple certificat médical peut ne pas être accepté (force majeure : hospitalisation, décès d'un parent, mission de travail) ; une commission décide du repassage.", "P-absence"),
    ("T1-04", "En cours du jour, il me faut combien de crédits pour être admis en année supérieure dès la session principale ?",
     "jour", "grading", [("D1-001", "Le nombre d’ECTS acquis pour l’année en cours doit être égal à 60 ECTS.")],
     "60 ECTS acquis pour l'année en cours, une moyenne générale ≥ 10/20 et aucun ECTS antérieur non validé.", ""),
    ("T1-05", "cours du soir : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?",
     "soir", "retakes", [("D1-002", "Déficit cumulé <= 10 ECTS (Il doit être égal à 0 ECTS si l'élève est en 4ème année)")],
     "Avec une moyenne générale ≥ 10/20 et un déficit cumulé ≤ 10 ECTS (0 ECTS en 4e année). Sinon, le dossier est soumis au Conseil annuel.", "P-passage"),
    ("T1-06", "Alternance : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?",
     "alternance", "retakes", [("D1-003", "Le nombre d’ECTS antérieurs cumulés non validés doit être inférieur ou égal à 12.")],
     "Avec une moyenne générale ≥ 10/20 et au plus 12 ECTS antérieurs non validés (0 en 4e année d'après le tableau) ; sinon l'élève est déclaré redoublant.", "P-passage"),
    ("T1-07", "j'ai raté 2 jours de cours pour raison médicale (cours du jour), j'ai combien de temps pour envoyer mon justificatif ?",
     "jour", "absences", [("D1-001", "un justificatif d’absence, dans un délai maximal d’une semaine.")],
     "Une semaine au maximum, au service de la scolarité.", "P-assiduite"),
    ("T1-08", "cours du soir : j'ai raté 2 jours de cours pour raison médicale, j'ai combien de temps pour envoyer mon justificatif ?",
     "soir", "absences", [("D1-002", "au plus tard le lendemain du début de l’empêchement."),
                          ("D1-002", "Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève.")],
     "Au plus tard le lendemain du début de l'empêchement (certificat médical ou justificatif au service de scolarité). Au-delà de 3 absences non justifiées dans un module : avertissement.", "P-assiduite"),
    ("T1-09", "En alternance on a le droit de redoubler combien de fois ?",
     "alternance", "retakes", [("D1-003", "Le redoublement est autorisé une seule fois au cours des quatre années de la scolarité.")],
     "Une seule fois sur les quatre années de la formation.", ""),
    ("T1-10", "Le stage d'immersion, c'est combien de semaines minimum et combien de crédits ?",
     "jour", "internships", [("D1-001", "Stage: Stage d'immersion en entreprise; Nombre d'ECTS: 3; Durée minimale: 6 semaines")],
     "6 semaines minimum, 3 ECTS, pendant l'été de la 3e année (1re année du cycle ingénieur).", ""),
    ("T1-11", "Cours du jour : si je me fais choper en train de tricher pendant un exam, ça se passe comment et je risque quoi ?",
     "jour", "discipline", [("D1-001", "le surveillant est tenu de récupérer les outils qui ont servi à la falsification et les annexer au procès-verbal"),
                            ("D1-001", "Les sanctions peuvent être sous forme d’avertissement, de blâme")],
     "Le surveillant récupère les outils de fraude et les annexe au procès-verbal ; un rapport de fraude est transmis et l'étudiant peut être conduit devant le conseil. Sanctions possibles : avertissement, blâme, interdiction d'une ou deux sessions, privation du rachat, privation de la mobilité internationale, exclusion jusqu'à un an, interdiction d'inscription jusqu'à deux ans, exclusion définitive.", ""),
    ("T1-12", "En cours du soir, si un prof trouve du plagiat dans mon rapport, j'aurai quelle note et quelles sanctions je risque ?",
     "soir", "discipline", [("D1-002", "la note de 0/20 est attribuée à l’UE"),
                            ("D1-002", "Renvoi de l’école pour une période maximale d’une année universitaire")],
     "0/20 à l'UE ; un rapport est adressé au directeur, qui peut réunir le conseil de discipline : avertissement, blâme, interdiction des examens d'une ou deux sessions, renvoi jusqu'à un an, renvoi définitif (sans remboursement des frais dans les deux derniers cas).", ""),
    ("T1-13", "cours du soir: je trouve ma note d'écrit trop basse, jusqu'à quand je peux demander une double correction et quelle note sera gardée ?",
     "soir", "grading", [("D1-002", "dans un délai d’une semaine après l’affichage de la note de cette épreuve"),
                         ("D1-008", "La note finale est la moyenne des deux corrections.")],
     "Dans la semaine qui suit l'affichage de la note, auprès du service examen (règlement officiel du cours du soir, art. 7-2). La note retenue (moyenne des deux corrections, 3e correction si l'écart dépasse 3 points) vient de la procédure FICTIVE D1-008 : à présenter comme non officielle.", ""),
    ("T1-14", "Cours du soir : on est en décembre, je peux encore demander un report d'inscription ?",
     "soir", "registration", [("D1-002", "Aucune demande de report d'inscription n'est recevable après le 30 novembre.")],
     "Non, aucune demande de report n'est recevable après le 30 novembre.", ""),
    ("T1-15", "Si mon contrat avec l'entreprise s'arrête, je peux continuer la formation en alternance ?",
     "alternance", "registration", [("D1-003", "entraîne l'exclusion automatique")],
     "Non : la rupture du contrat de travail entraîne l'exclusion automatique de la formation. Une réintégration dépend de l'avis de l'entreprise, de la décision du conseil de discipline avec l'accord de la direction des études, et du remboursement des frais engagés.", ""),
    ("T1-16", "en alternance, les UE qui sont que du TP, on peut les rattraper ?",
     "alternance", "retakes", [("D1-003", "n’ont pas d’examen final et ne peuvent pas faire l’objet de rattrapage.")],
     "Non : les UE organisées uniquement en TP ou travaux personnalisés n'ont pas d'examen final et ne sont pas rattrapables.", ""),
    ("T1-17", "je suis super stressé avec les exams, il y a quelqu'un à qui parler à l'école ?",
     "jour", "campus life", [("D1-001", "La cellule d’écoute et d’accompagnement est un espace confidentiel")],
     "Oui : la cellule d'écoute et d'accompagnement, espace confidentiel et volontaire qui accueille, écoute et oriente les élèves (scolarité, stress, anxiété, mal-être).", ""),
    ("T1-18", "J'ai besoin d'un aménagement pour les examens (tiers temps), je dois déposer quoi et avant quand ?",
     "all", "exams", [("D1-005", "Le dossier comprend le formulaire FORM-04, un document médical récent établi par un médecin et une pièce d'identité.")],
     "Selon la procédure FICTIVE D1-005 : formulaire FORM-04, document médical récent et pièce d'identité, déposés à la scolarité au moins 7 jours avant la session. À présenter comme non officiel ; le règlement officiel (cours du jour, art. 7-8) prévoit seulement un dossier médical déposé au préalable à la scolarité.", ""),
    ("T1-19", "En combien de temps on obtient un relevé de notes ?",
     "all", "registration", [("D1-006", "relevé de notes, 7 jours ouvrables à partir de la")],
     "Selon la procédure FICTIVE D1-006 : 7 jours ouvrables à partir de la publication officielle des résultats, demande à la scolarité (FORM-03 + pièce d'identité). Non officiel.", ""),
    ("T1-20", "Je dois signer une convention avant de commencer mon stage d'été ? et si je l'ai pas ?",
     "jour", "internships", [("D1-010", "Un stage commencé sans convention signée n'est pas reconnu par l'école.")],
     "Selon le guide FICTIF D1-010 : oui, une convention tripartite signée avant le premier jour et déposée au service des stages ; sinon le stage n'est pas reconnu. Non officiel.", ""),
    ("T1-21", "Pour faire une demande de repassage exceptionnel, je dois apporter quels papiers ?",
     "all", "retakes", [("D1-004", "le formulaire de demande de repassage exceptionnel (modèle FORM-01)")],
     "Selon la procédure FICTIVE D1-004 : formulaire FORM-01, pièce d'identité, justificatif officiel original et sa copie, déposés à la scolarité. Le règlement officiel (cours du jour, art. 7-8) dit seulement que le dossier est déposé auprès de la scolarité.", ""),
    ("T1-22", "Mon rapport de PFE doit etre rendu combien de jours avant la soutenance ?",
     "all", "internships", [("D1-007", "Le rapport complet est déposé au plus tard 15 jours avant la date de soutenance.")],
     "Selon la procédure FICTIVE D1-007 : au plus tard 15 jours avant la soutenance. Les règlements officiels ne fixent pas de délai.", ""),
    ("T1-23", "C'est combien exactement les frais de scolarité en 4ème année cours du jour ?",
     "jour", "registration", [], "Information non trouvée dans les règlements : orienter vers le service financier (FIN).", ""),
    ("T1-24", "La bibliothèque est ouverte jusqu'à quelle heure le samedi ?",
     "all", "campus life", [], "Information non trouvée : orienter vers la scolarité (contact général, SCO-GEN).", ""),
    ("T1-25", "Je peux faire mon stage ingénieur à l'étranger ? il y a des démarches spéciales ?",
     "jour", "internships", [], "Information non trouvée dans les règlements : orienter vers le département des stages (STAGE) et la mobilité internationale (MOB).", ""),
]
UNANSWERABLE_SEARCH = {"T1-23": ["dinars", "montant des frais", "tnd"],
                       "T1-24": ["horaire de la bibliothèque", "bibliothèque est ouverte", "horaires d'ouverture"],
                       "T1-25": ["étranger", "stage à l'international"]}


def main() -> None:
    verified = json.loads(VERIFIED.read_text(encoding="utf-8")) if VERIFIED.exists() else {}
    corpus = {i: canon(" ".join(p["text"] for p in doc(i)["pages"])) for i in all_doc_ids()}
    csv_rows, review, errors = [], [], []
    for rid, q, regime, topic, srcs, ans, pair in ROWS:
        keys, pages, docs, run = [], [], [], 0
        for d, quote in srcs:
            f = find_quote(d, quote)
            if not f or not f["key"]:
                errors.append(f"{rid}: quote not found in {d}: {quote[:60]}")
                continue
            keys.append(f["key"]); pages.append(str(f["page"])); docs.append(d)
            unit = next(u["text"] for u in doc(d)["articles"] if u["key"] == f["key"])
            run = max(run, longest_shared_run(q, unit))
        if run > 5:
            errors.append(f"{rid}: question reuses {run} consecutive words of its source")
        if not srcs:
            hits = {t: sum(c.count(canon(t)) for c in corpus.values()) for t in UNANSWERABLE_SEARCH[rid]}
            if any(hits.values()):
                errors.append(f"{rid}: unanswerable but search terms hit {hits}")
        dedup = lambda xs: "|".join(dict.fromkeys(xs))
        csv_rows.append({"id": rid, "question": q, "regime": regime, "topic": topic, "expected_doc_id": dedup(docs),
                         "expected_article": dedup(keys), "expected_page": dedup(pages), "expected_answer": ans,
                         "answerable": "yes" if srcs else "no", "verified_by": verified.get(rid, "")})
        lines = [f"### {rid} — {topic} · regime `{regime}`" + (f" · pair `{pair}`" if pair else "") +
                 (" · **spans two articles**" if len(set(keys)) > 1 else ""),
                 f"- **Question**: {q}", f"- **Proposed answer**: {ans}"]
        for d, quote in srcs:
            f = find_quote(d, quote)
            status = doc(d)["doc_status"]
            lines.append(f"- **Source** {d} ({status}) · `{f['key'] if f else '?'}` · p.{f['page'] if f else '?'}: « {quote} »")
        if not srcs:
            lines.append(f"- **Unanswerable**: searched {UNANSWERABLE_SEARCH[rid]} → no match in the 11 documents.")
        lines += [f"- Max consecutive words shared with the source: {run}", "- [ ] OK  [ ] fix: ____", ""]
        review += lines
    # coverage checks (plan §3.6 + A5)
    reg = collections.Counter(r["regime"] for r in csv_rows if r["answerable"] == "yes")
    fict = sum(1 for r in csv_rows if any(doc(d)["doc_status"] == "FICTITIOUS" for d in r["expected_doc_id"].split("|") if d))
    pairs = collections.Counter(p for *_, p in ROWS if p)
    spans = sum(1 for r in csv_rows if "|" in r["expected_article"])
    unans = sum(1 for r in csv_rows if r["answerable"] == "no")
    topics = sorted({r["topic"] for r in csv_rows})
    checks = {"rows == 25": len(csv_rows) == 25, "jour >= 5": reg["jour"] >= 5, "soir >= 5": reg["soir"] >= 5,
              "alternance >= 5": reg["alternance"] >= 5, "FICTITIOUS-sourced >= 5": fict >= 5,
              "regime pair groups 3-4": 3 <= len(pairs) <= 4, "two-article questions 2-3": 2 <= spans <= 3,
              "unanswerable == 3": unans == 3,
              "topics cover exams/retakes/absences/grading/internships/discipline/registration":
                  {"exams", "retakes", "absences", "grading", "internships", "discipline", "registration"} <= set(topics)}
    summary = [f"- regimes (answerable): {dict(reg)}; FICTITIOUS-sourced rows: {fict}; pair groups: {dict(pairs)};",
               f"  two-article rows: {spans}; unanswerable: {unans}; topics: {topics}"] + \
              [f"- {'✅' if ok else '❌'} {name}" for name, ok in checks.items()]
    if errors or not all(checks.values()):
        print("\n".join(errors + summary)); sys.exit(1)
    with open(ROOT / "eval/T1_regulations.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0])); w.writeheader(); w.writerows(csv_rows)
    head = ["# T1 review sheet — 25 regulation questions (CF-111)", "",
            "Each row: tick **OK** if the proposed answer is exactly what the quoted source says, or write the fix.",
            "Quotes were located verbatim in `data/regs/clean/` by `scripts/build_t1.py`; article keys and pages are",
            "derived from them (A4). FICTITIOUS sources must be presented as non-official (A2).", "", "## Coverage", ""] + summary + ["", "## Rows", ""]
    (ROOT / "eval/review/T1_review.md").write_text("\n".join(head + review) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(summary)); print(f"verified rows: {sum(1 for r in csv_rows if r['verified_by'])}/25")


if __name__ == "__main__":
    main()
