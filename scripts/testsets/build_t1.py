"""CF-111 — build the T1 regulation test set, its review sheet and the claim-level evidence check.

Every expected answer is a list of CLAIMS; each factual claim carries evidence that is checked automatically:
  ("q", doc_id, quote)        verbatim quote located in data/regs/clean/ (→ article key + page)
  ("absent", doc_ids, terms)  none of the terms occurs in those documents (negative claims, "not found")
  ("table", file, row, field, text)  the text occurs in that cell of data/tables/<file>.csv
Claims of kind "note" are presentation rules (e.g. "present as non-official"), not facts.
expected_article = the article keys of the accepted sources, separated by "|" (used by Hit@5 / Recall@5 / MRR).
The A5 rule (no more than 5 consecutive words copied from a source article) and the coverage rules are enforced.
Outputs: eval/testsets/T1_regulations.csv, eval/review/sheets/T1_review.md, eval/review/ticks/T1_changed_rows.md (vs the reviewed version)
Run: .venv/Scripts/python scripts/testsets/build_t1.py
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "lib"), str(Path(__file__).resolve().parent)]
from corpus_lookup import all_doc_ids, canon, doc, find_quote, longest_shared_run, write_review  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
VERIFIED = ROOT / "eval/review/verified/T1_verified.json"   # {"T1-01": "Fedi", ...}
PREVIOUS = ROOT / ".superpowers/T1_review_v1.md"   # the sheet Fedi reviewed (for the changed-rows report)
OFFICIAL = ["D1-001", "D1-002", "D1-003"]
NOTE_FICTIF = ("note", "Source FICTIVE : à présenter comme non officielle (règle de précédence A2).")


def q(d, quote):
    return ("q", d, quote)


C = lambda text, *ev: (text, list(ev))  # a factual claim with its evidence

# id, question, regime, topic, pair group, claims
ROWS = [
    ("T1-01", "Jsuis tombé malade le jour de mon exam final (grosse migraine), j'ai un certif du médecin : ça suffit pour le repasser ?", "jour", "absences", "P-absence", [
        C("Non : en cours du jour, un certificat médical n'est pas un justificatif d'absence.", q("D1-001", "Les certificats médicaux ne constituent pas un justificatif d’absence.")),
        C("Seuls un accident, une maladie contagieuse, une hospitalisation ou le décès d'un parent proche justifient une absence à une épreuve finale.",
          q("D1-001", "Seuls les cas d’accidents, de maladies contagieuses, d’hospitalisations où de décès d’un parent proche sont considérés comme justificatif d’absence à une épreuve finale.")),
        C("L'étudiant peut déposer un dossier de repassage exceptionnel à la scolarité, traité au cas par cas.",
          q("D1-001", "Toutefois, les demandes de repassage exceptionnelles sont traitées au cas par cas et se font suite à un dépôt de dossier auprès de la scolarité"))]),
    ("T1-02", "Cours du soir : j'ai loupé l'examen à cause d'une migraine et j'ai seulement un certificat médical, est-ce que ça marche ?", "soir", "absences", "P-absence", [
        C("Non : un simple certificat médical n'est pas un motif valable.", q("D1-002", "Il est à noter qu’un simple certificat médical n'est pas considéré comme un motif valable.")),
        C("Seule la force majeure (hospitalisation, décès d'un parent ou mission de travail) est prise en compte : il faut aviser le responsable de la scolarité dans les 48 h suivant l'épreuve, avec les pièces justificatives.",
          q("D1-002", "en cas d’empêchement dû à une force majeure (hospitalisation, décès d’un parent ou mission de travail), l’élève doit aviser le responsable de la scolarité dans un délai ne dépassant pas 48h à compter de la date de l’épreuve avec remise des pièces justificatives.")),
        C("Une commission désignée par la direction de l'école étudie le cas et accorde ou refuse le repassage.",
          q("D1-002", "Une commission désignée par la direction de l’école étudie les différents cas et peut accorder ou refuser le repassage de l’examen."))]),
    ("T1-03", "Je suis en alternance et j'étais malade le jour d'un examen, j'ai qu'un certificat du médecin. Je fais comment ?", "alternance", "absences", "P-absence", [
        C("En cas de force majeure (hospitalisation, décès d'un parent ou mission de travail), l'alternant avise le responsable de la scolarité dans les 48 h suivant l'épreuve, avec les pièces justificatives.",
          q("D1-003", "en cas d’empêchement dû à une force majeure (hospitalisation, décès d’un parent ou mission de travail), l’alternant doit aviser le responsable de la scolarité dans un délai ne dépassant pas 48h à compter de la date de l’épreuve avec remise des pièces justificatives.")),
        C("Un simple certificat médical peut ne pas être accepté.", q("D1-003", "un simple certificat médical peut ne pas être considéré comme un motif valable")),
        C("Une commission désignée par la direction de l'école étudie le cas et accorde ou refuse le repassage.",
          q("D1-003", "Une commission désignée par la direction de l’école étudie les différents cas et peut accorder ou refuser le repassage de l’examen."))]),
    ("T1-04", "En cours du jour, il me faut combien de crédits pour être admis en année supérieure dès la session principale ?", "jour", "grading", "", [
        C("60 ECTS acquis pour l'année en cours.", q("D1-001", "Le nombre d’ECTS acquis pour l’année en cours doit être égal à 60 ECTS.")),
        C("Une moyenne générale d'au moins 10/20.", q("D1-001", "La moyenne générale doit être supérieure ou égale à 10/20.")),
        C("Aucun ECTS antérieur non validé.", q("D1-001", "Le nombre d’ECTS antérieurs cumulés non validés doit être nul."))]),
    ("T1-05", "cours du soir : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?", "soir", "retakes", "P-passage", [
        C("Après le rattrapage : moyenne générale ≥ 10/20 et déficit cumulé ≤ 10 ECTS (0 ECTS en 4e année).",
          q("D1-002", "Session: Rattrapage; Conditions d'admission: • Moyenne générale >= 10/20 • Déficit cumulé <= 10 ECTS (Il doit être égal à 0 ECTS si l'élève est en 4ème année)")),
        C("Sinon, le cas est soumis au Conseil annuel pour délibération.", q("D1-002", "sont considérés comme des cas spécifiques qui seront soumis au « Conseil Annuel » pour délibération"))]),
    ("T1-06", "Alternance : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?", "alternance", "retakes", "P-passage", [
        C("Moyenne générale ≥ 10/20.", q("D1-003", "La moyenne générale doit être supérieure ou égale à 10/20.")),
        C("Au plus 12 ECTS antérieurs non validés.", q("D1-003", "Le nombre d’ECTS antérieurs cumulés non validés doit être inférieur ou égal à 12.")),
        C("0 ECTS de déficit si l'élève est en 4e année.", q("D1-003", "Déficit cumulé <= 12 ECTS (Il doit être égal à 0 ECTS si l'élève est en 4ème année)")),
        C("Sinon, l'élève est déclaré redoublant.", q("D1-003", "n’ayant pas satisfait les conditions précitées d’admission en année supérieure seront déclaré redoublants"))]),
    ("T1-07", "j'ai raté 2 jours de cours pour raison médicale (cours du jour), j'ai combien de temps pour envoyer mon justificatif ?", "jour", "absences", "P-assiduite", [
        C("Une semaine au maximum, au service de la scolarité.", q("D1-001", "l’élève doit adresser au service de scolarité un justificatif d’absence, dans un délai maximal d’une semaine."))]),
    ("T1-08", "cours du soir : j'ai raté 2 jours de cours pour raison médicale, j'ai combien de temps pour envoyer mon justificatif ?", "soir", "absences", "P-assiduite", [
        C("Au plus tard le lendemain du début de l'empêchement : certificat médical ou justificatif au service de scolarité.",
          q("D1-002", "l’élève doit adresser au Service de Scolarité un certificat médical ou un justificatif, au plus tard le lendemain du début de l’empêchement.")),
        C("Au-delà de 3 absences non justifiées dans un module : avertissement.", q("D1-002", "Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève."))]),
    ("T1-09", "En alternance on a le droit de redoubler combien de fois ?", "alternance", "retakes", "", [
        C("Une seule fois sur les quatre années de la scolarité.", q("D1-003", "Le redoublement est autorisé une seule fois au cours des quatre années de la scolarité."))]),
    ("T1-10", "Le stage d'immersion, c'est combien de semaines minimum et combien de crédits ?", "jour", "internships", "", [
        C("6 semaines minimum et 3 ECTS.", q("D1-001", "Stage: Stage d'immersion en entreprise; Nombre d'ECTS: 3; Durée minimale: 6 semaines")),
        C("Pendant l'été de la 3e année (1re année du cycle ingénieur).", q("D1-001", "Période: durant l'été de la 3ème année (1ère année cycle ingénieur)"))]),
    ("T1-11", "Cours du jour : si je me fais choper en train de tricher pendant un exam, ça se passe comment et je risque quoi ?", "jour", "discipline", "", [
        C("Le surveillant récupère les outils de fraude et les annexe au procès-verbal.",
          q("D1-001", "le surveillant est tenu de récupérer les outils qui ont servi à la falsification et les annexer au procès-verbal")),
        C("Un rapport de fraude est déposé auprès du chef de département de la scolarité.", q("D1-001", "Un rapport de fraude est déposé auprès du chef de département de la scolarité")),
        C("La fraude peut conduire l'étudiant devant le conseil de discipline.", q("D1-001", "peut conduire son auteur devant le conseil de discipline")),
        C("Sanctions possibles : avertissement, blâme, interdiction d'une ou deux sessions d'examen, privation du rachat, privation de la mobilité internationale, exclusion d'un an au maximum, interdiction provisoire d'inscription de deux ans au maximum, exclusion définitive.",
          q("D1-001", "Les sanctions peuvent être sous forme d’avertissement, de blâme, d'interdiction de participation à une ou deux des sessions d'examen, de privation du rachat, de privation de la mobilité internationale, d’exclusion de l'école pour une période d'une année universitaire au maximum, d'interdiction provisoire d’inscription à l'établissement pour une période de deux années universitaires au maximum ou de l'exclusion définitive de l'école."))]),
    ("T1-12", "En cours du soir, si un prof trouve du plagiat dans mon rapport, j'aurai quelle note et quelles sanctions je risque ?", "soir", "discipline", "", [
        C("0/20 à l'UE.", q("D1-002", "Lorsqu’un plagiat est constaté, la note de 0/20 est attribuée à l’UE.")),
        C("Un rapport est adressé au directeur, qui peut réunir le conseil de discipline.",
          q("D1-002", "Un rapport est adressé au directeur de l’école qui peut réunir le conseil de discipline pour décider de la sanction à adresser au plagiaire.")),
        C("Sanctions possibles : avertissement, blâme, interdiction des examens d'une ou deux sessions, renvoi d'un an au maximum, renvoi définitif.",
          q("D1-002", "1. Avertissement"), q("D1-002", "2. Blâme"), q("D1-002", "3. Interdiction de passer les examens d’une ou deux sessions"),
          q("D1-002", "4. Renvoi de l’école pour une période maximale d’une année universitaire"), q("D1-002", "5. Renvoi définitif de l’École")),
        C("Pas de remboursement des frais de scolarité dans les deux derniers cas.", q("D1-002", "Dans les deux derniers cas, l’élève n’a pas le droit au remboursement des frais de scolarité."))]),
    ("T1-13", "cours du soir: je trouve ma note d'écrit trop basse, jusqu'à quand je peux demander une double correction et quelle note sera gardée ?", "soir", "grading", "", [
        C("Dans la semaine qui suit l'affichage de la note, auprès du service examen (règlement officiel du cours du soir).",
          q("D1-002", "L’étudiant peut déposer une demande de double correction d’une épreuve écrite auprès de service examen dans un délai d’une semaine après l’affichage de la note de cette épreuve.")),
        C("Note retenue : la moyenne des deux corrections.", q("D1-008", "La note finale est la moyenne des deux corrections.")),
        C("Troisième correction si l'écart dépasse 3 points sur 20.", q("D1-008", "Si l'écart entre les deux notes dépasse 3 points sur 20, une troisième correction est effectuée")),
        NOTE_FICTIF]),
    ("T1-14", "Cours du soir : on est en décembre, je peux encore demander un report d'inscription ?", "soir", "registration", "", [
        C("Non : aucune demande de report n'est recevable après le 30 novembre.", q("D1-002", "Aucune demande de report d'inscription n'est recevable après le 30 novembre."))]),
    ("T1-15", "Si mon contrat avec l'entreprise s'arrête, je peux continuer la formation en alternance ?", "alternance", "registration", "", [
        C("Non : la rupture du contrat de travail entraîne l'exclusion automatique de la formation.",
          q("D1-003", "La rupture du contrat de travail, quelle qu'en soit la raison (démission, résiliation ou autre), entraîne l'exclusion automatique de la formation à ESPRIT.")),
        C("La réintégration dépend de l'avis de l'entreprise, de la décision du conseil de discipline avec l'accord de la direction des études, et du remboursement des frais engagés.",
          q("D1-003", "1- L'avis de l'entreprise partenaire"), q("D1-003", "2- La décision du conseil de discipline et l'accord de la direction des études"),
          q("D1-003", "3- Le remboursement de tous les frais engagés durant son parcours de formation en alternance."))]),
    ("T1-16", "en alternance, les UE qui sont que du TP, on peut les rattraper ?", "alternance", "retakes", "", [
        C("Non : les UE organisées uniquement en TP ou travaux personnalisés n'ont pas d'examen final et ne sont pas rattrapables.",
          q("D1-003", "Les UEs qui sont organisées exclusivement sous forme de travaux pratiques ou de travaux personnalisés n’ont pas d’examen final et ne peuvent pas faire l’objet de rattrapage."))]),
    ("T1-17", "je suis super stressé avec les exams, il y a quelqu'un à qui parler à l'école ?", "all", "campus life", "", [
        C("Oui : la cellule d'écoute et d'accompagnement, espace confidentiel qui accueille, écoute, informe et oriente les élèves.",
          q("D1-001", "La cellule d’écoute et d’accompagnement est un espace confidentiel qui a pour objectif d’accueillir, écouter, comprendre, informer et orienter les élèves"),
          q("D1-003", "La cellule d’écoute et d’accompagnement est un espace confidentiel qui a pour objectif d’accueillir, écouter, comprendre, informer et orienter les élèves")),
        C("La démarche est volontaire.", q("D1-001", "cette démarche doit rester volontaire")),
        C("Domaines : scolarité, stress/anxiété, tristesse, mal-être.", q("D1-001", "(scolarité, stress/anxiété, tristesse, mal être diffus…)"))]),
    ("T1-18", "J'ai besoin d'un aménagement pour les examens (tiers temps), je dois déposer quoi et avant quand ?", "all", "exams", "", [
        C("Le dossier comprend le formulaire FORM-04, un document médical récent et une pièce d'identité.",
          q("D1-005", "Le dossier comprend le formulaire FORM-04, un document médical récent établi par un médecin et une pièce d'identité.")),
        C("Il est déposé à la scolarité au moins 7 jours avant le début de la session.", q("D1-005", "Il est déposé à la scolarité au moins 7 jours avant le début de la session d'examens.")),
        C("Le règlement officiel (cours du jour) prévoit seulement un dossier médical déposé au préalable à la scolarité.",
          q("D1-001", "sont demandés à déposer un dossier médical à la scolarité au préalable afin d’avoir le consentement")),
        NOTE_FICTIF]),
    ("T1-19", "En combien de temps on obtient un relevé de notes ?", "all", "registration", "", [
        C("7 jours ouvrables à partir de la publication officielle des résultats.", q("D1-006", "relevé de notes, 7 jours ouvrables à partir de la publication officielle des résultats")),
        C("Demande au service de la scolarité avec le formulaire FORM-03 et une pièce d'identité.",
          q("D1-006", "La demande se fait auprès du service de la scolarité avec le formulaire FORM-03 et une pièce d'identité")),
        NOTE_FICTIF]),
    ("T1-20", "Je dois signer une convention avant de commencer mon stage d'été ? et si je l'ai pas ?", "jour", "internships", "", [
        C("Oui : une convention tripartite est signée avant le premier jour de stage et déposée au service des stages.",
          q("D1-010", "Avant le premier jour de stage, une convention de stage tripartite (étudiant, école, organisme d'accueil) est signée par les trois parties et déposée auprès du service des stages.")),
        C("Sans convention signée, le stage n'est pas reconnu.", q("D1-010", "Un stage commencé sans convention signée n'est pas reconnu par l'école.")),
        NOTE_FICTIF]),
    ("T1-21", "Pour faire une demande de repassage exceptionnel, je dois apporter quels papiers ?", "all", "retakes", "", [
        C("Le formulaire FORM-01, une pièce d'identité, et le justificatif officiel original avec une copie.",
          q("D1-004", "le formulaire de demande de repassage exceptionnel (modèle FORM-01)"), q("D1-004", "une pièce d'identité (CIN, passeport ou carte d'étudiant)"),
          q("D1-004", "le justificatif officiel original (attestation d'hospitalisation, acte de décès, attestation de l'autorité compétente, ordre de mission pour l'alternance), accompagné d'une copie")),
        C("Le dossier est déposé auprès du service de la scolarité.", q("D1-004", "Le dossier est déposé auprès du service de la scolarité")),
        C("Le règlement officiel (cours du jour) dit seulement que le dossier est déposé auprès de la scolarité.",
          q("D1-001", "se font suite à un dépôt de dossier auprès de la scolarité")),
        NOTE_FICTIF]),
    ("T1-22", "Mon rapport de PFE doit etre rendu combien de jours avant la soutenance ?", "all", "internships", "", [
        C("Au plus tard 15 jours avant la soutenance.", q("D1-007", "Le rapport complet est déposé au plus tard 15 jours avant la date de soutenance.")),
        C("Les règlements officiels ne fixent pas ce délai.", ("absent", OFFICIAL, ["jours avant la date de soutenance", "jours avant la soutenance", "avant la soutenance"])),
        NOTE_FICTIF]),
    ("T1-23", "C'est combien exactement les frais de scolarité en 4ème année cours du jour ?", "jour", "registration", "", [
        C("Information non trouvée dans les 11 documents.", ("absent", None, ["dinars", "montant des frais", "tnd"])),
        C("Orienter vers le service financier (FIN).", ("table", "directory", "FIN", "handles", "Frais de scolarité"))]),
    ("T1-24", "La bibliothèque est ouverte jusqu'à quelle heure le samedi ?", "all", "campus life", "", [
        C("Information non trouvée dans les 11 documents.", ("absent", None, ["horaire de la bibliothèque", "bibliothèque est ouverte", "horaires d'ouverture"])),
        C("Orienter vers la scolarité, contact général (SCO-GEN).", ("table", "directory", "SCO-GEN", "handles", "Questions générales de scolarité"))]),
    ("T1-25", "Je peux faire mon stage ingénieur à l'étranger ? il y a des démarches spéciales ?", "jour", "internships", "", [
        C("Information non trouvée dans les 11 documents.", ("absent", None, ["étranger", "stage à l'international"])),
        C("Orienter vers le département des stages (STAGE) et la mobilité internationale (MOB).",
          ("table", "directory", "STAGE", "handles", "suivi des stages"), ("table", "directory", "MOB", "handles", "Échanges internationaux"))]),
]


def check_evidence(ev) -> tuple[bool, str, str | None, str | None]:
    """Return (ok, human-readable evidence line, article key, page)."""
    kind = ev[0]
    if kind == "q":
        f = find_quote(ev[1], ev[2])
        st = doc(ev[1])["doc_status"]
        return (bool(f and f["key"]), f"{ev[1]} ({st}) · `{f['key'] if f else '?'}` · p.{f['page'] if f else '?'}: « {ev[2]} »",
                f["key"] if f else None, str(f["page"]) if f else None)
    if kind == "absent":
        ids = ev[1] or all_doc_ids()
        hits = {t: sum(canon(" ".join(p["text"] for p in doc(i)["pages"])).count(canon(t)) for i in ids) for t in ev[2]}
        scope = "official regulations D1-001…003" if ev[1] else "the 11 documents"
        return not any(hits.values()), f"absence check in {scope}: {hits}", None, None
    if kind == "table":
        _, f, rid, field, text = ev
        rows = {r[next(iter(r))]: r for r in csv.DictReader(open(ROOT / f"data/tables/{f}.csv", encoding="utf-8"))}
        cell = rows.get(rid, {}).get(field, "")
        return canon(text) in canon(cell), f"data/tables/{f}.csv · {rid}.{field}: « {cell} »", None, None
    return False, f"unknown evidence {ev}", None, None


def previous_quotes() -> dict:
    """Quotes per row in the sheet Fedi reviewed (to report changed rows)."""
    out, cur = collections.defaultdict(set), None
    if PREVIOUS.exists():
        for ln in PREVIOUS.read_text(encoding="utf-8").splitlines():
            m = re.match(r"### (T1-\d+)", ln)
            cur = m.group(1) if m else cur
            m = re.search(r"« (.*) »$", ln)
            if cur and m and ln.startswith("- **Source**"):
                out[cur].add(canon(m.group(1)))
    return out


def main() -> None:
    verified = json.loads(VERIFIED.read_text(encoding="utf-8")) if VERIFIED.exists() else {}
    old_rows = {r["id"]: r for r in csv.DictReader(open(ROOT / ".superpowers/T1_v1.csv", encoding="utf-8"))} if (ROOT / ".superpowers/T1_v1.csv").exists() else {}
    old_q = previous_quotes()
    csv_rows, review, changed, reworded, errors = [], [], [], [], []
    for rid, question, regime, topic, pair, claims in ROWS:
        keys, pages, docs, run, lines, quotes = [], [], [], 0, [], set()
        answer = " ".join(c[0] if isinstance(c, tuple) and c[0] != "note" else c[1] for c in claims)
        for c in claims:
            if c[0] == "note":
                lines.append(f"  - *(note)* {c[1]}")
                continue
            text, evs = c
            if not evs:
                errors.append(f"{rid}: claim without evidence: {text}")
            lines.append(f"  - **Claim**: {text}")
            for ev in evs:
                ok, desc, key, page = check_evidence(ev)
                if not ok:
                    errors.append(f"{rid}: evidence failed: {desc[:120]}")
                lines.append(f"    - {'✔' if ok else '✘'} {desc}")
                if key:
                    keys.append(key); pages.append(page); docs.append(key.split("/")[0]); quotes.add(canon(ev[2]))
                    unit = next(u["text"] for u in doc(ev[1])["articles"] if u["key"] == key)
                    run = max(run, longest_shared_run(question, unit))
        if run > 5:
            errors.append(f"{rid}: question reuses {run} consecutive words of its source")
        dedup = lambda xs: "|".join(dict.fromkeys(xs))
        row = {"id": rid, "question": question, "regime": regime, "topic": topic, "expected_doc_id": dedup(docs),
               "expected_article": dedup(keys), "expected_page": dedup(pages), "expected_answer": answer,
               "answerable": "yes" if keys else "no", "verified_by": ""}
        old = old_rows.get(rid)
        # substantive change = new evidence, other article keys or other regime (rewording into claims is not a change)
        new_quotes = quotes - old_q.get(rid, set())
        is_changed = (not old) or old["expected_article"] != row["expected_article"] or old["regime"] != regime or bool(new_quotes)
        if is_changed and rid not in verified:
            changed.append(rid)
        if not is_changed and old and old["expected_answer"] != answer:
            reworded.append(rid)
        row["verified_by"] = verified.get(rid, "")
        csv_rows.append(row)
        head = (f"### {rid} — {topic} · regime `{regime}`" + (f" · pair `{pair}`" if pair else "") +
                (" · **multi-source**" if "|" in row["expected_article"] else "") + (" · **CHANGED**" if is_changed else ""))
        block = [head, f"- **Question**: {question}", f"- **expected_article**: `{row['expected_article'] or '—'}`", *lines,
                 f"- Max consecutive words shared with the sources: {run}", "- [ ] OK  [ ] fix: ____", ""]
        review += block
    reg = collections.Counter(r["regime"] for r in csv_rows if r["answerable"] == "yes")
    fict = sum(1 for r in csv_rows if any(doc(d)["doc_status"] == "FICTITIOUS" for d in r["expected_doc_id"].split("|") if d))
    pairs = collections.Counter(p for _, _, _, _, p, _ in ROWS if p)
    multi = sum(1 for r in csv_rows if "|" in r["expected_article"])
    unans = sum(1 for r in csv_rows if r["answerable"] == "no")
    topics = sorted({r["topic"] for r in csv_rows})
    checks = {"rows == 25": len(csv_rows) == 25, "jour >= 5": reg["jour"] >= 5, "soir >= 5": reg["soir"] >= 5,
              "alternance >= 5": reg["alternance"] >= 5, "FICTITIOUS-sourced >= 5": fict >= 5,
              "regime pair groups 3-4": 3 <= len(pairs) <= 4, "multi-source rows >= 2": multi >= 2, "unanswerable == 3": unans == 3,
              "topics cover the scope": {"exams", "retakes", "absences", "grading", "internships", "discipline", "registration"} <= set(topics),
              "every factual claim has passing evidence": not errors}
    summary = [f"- regimes (answerable): {dict(reg)}; FICTITIOUS-sourced rows: {fict}; pair groups: {dict(pairs)};",
               f"  multi-source rows: {multi}; unanswerable: {unans}; topics: {topics}"] + [f"- {'✅' if ok else '❌'} {n}" for n, ok in checks.items()]
    if errors or not all(checks.values()):
        print("\n".join(errors + summary)); sys.exit(1)
    with open(ROOT / "eval/testsets/T1_regulations.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(csv_rows)
    intro = ["# T1 review sheet — 25 regulation questions (CF-111)", "",
             "Claim-level evidence: every factual claim of the expected answer is backed by a verbatim quote (doc_id, article key,",
             "page), an absence check or a table cell — all checked automatically by `scripts/testsets/build_t1.py`.", "", "## Coverage", ""]
    write_review(ROOT / "eval/review/sheets/T1_review.md", "\n".join(intro + summary + ["", "## Rows", ""] + review) + "\n")
    ch = ["# T1 — rows changed since your review (final tick)", "",
          f"{len(changed)} rows with new evidence, other keys or another regime: {', '.join(changed)}",
          f"Reworded into claims only (same quotes, same keys — already verified if you accepted them): {', '.join(reworded) or '—'}", "",
          "## Rows", ""]
    ch += [ln for blk in "\n".join(review).split("### ")[1:] if blk.split(" ")[0] in changed for ln in ("### " + blk).splitlines()]
    write_review(ROOT / "eval/review/ticks/T1_changed_rows.md", "\n".join(ch) + "\n")
    print("\n".join(summary)); print(f"verified rows: {sum(1 for r in csv_rows if r['verified_by'])}/25 · changed rows to tick: {changed}")


if __name__ == "__main__":
    main()
