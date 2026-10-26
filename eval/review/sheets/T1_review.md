# T1 review sheet — 25 regulation questions (CF-111)

Claim-level evidence: every factual claim of the expected answer is backed by a verbatim quote (doc_id, article key,
page), an absence check or a table cell — all checked automatically by `scripts/testsets/build_t1.py`.

## Coverage

- regimes (answerable): {'jour': 6, 'soir': 6, 'alternance': 5, 'all': 5}; FICTITIOUS-sourced rows: 6; pair groups: {'P-absence': 3, 'P-passage': 2, 'P-assiduite': 2};
  multi-source rows: 6; unanswerable: 3; topics: ['absences', 'campus life', 'discipline', 'exams', 'grading', 'internships', 'registration', 'retakes']
- ✅ rows == 25
- ✅ jour >= 5
- ✅ soir >= 5
- ✅ alternance >= 5
- ✅ FICTITIOUS-sourced >= 5
- ✅ regime pair groups 3-4
- ✅ multi-source rows >= 2
- ✅ unanswerable == 3
- ✅ topics cover the scope
- ✅ every factual claim has passing evidence

## Rows

### T1-01 — absences · regime `jour` · pair `P-absence` · **CHANGED**
- **Question**: Jsuis tombé malade le jour de mon exam final (grosse migraine), j'ai un certif du médecin : ça suffit pour le repasser ?
- **expected_article**: `D1-001/7-8/Déroulement des épreuves`
  - **Claim**: Non : en cours du jour, un certificat médical n'est pas un justificatif d'absence.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Les certificats médicaux ne constituent pas un justificatif d’absence. »
  - **Claim**: Seuls un accident, une maladie contagieuse, une hospitalisation ou le décès d'un parent proche justifient une absence à une épreuve finale.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Seuls les cas d’accidents, de maladies contagieuses, d’hospitalisations où de décès d’un parent proche sont considérés comme justificatif d’absence à une épreuve finale. »
  - **Claim**: L'étudiant peut déposer un dossier de repassage exceptionnel à la scolarité, traité au cas par cas.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Toutefois, les demandes de repassage exceptionnelles sont traitées au cas par cas et se font suite à un dépôt de dossier auprès de la scolarité »
- Max consecutive words shared with the sources: 1
- [ ] OK  [ ] fix: ____

### T1-02 — absences · regime `soir` · pair `P-absence` · **CHANGED**
- **Question**: Cours du soir : j'ai loupé l'examen à cause d'une migraine et j'ai seulement un certificat médical, est-ce que ça marche ?
- **expected_article**: `D1-002/7-2/Evaluation des élèves`
  - **Claim**: Non : un simple certificat médical n'est pas un motif valable.
    - ✔ D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « Il est à noter qu’un simple certificat médical n'est pas considéré comme un motif valable. »
  - **Claim**: Seule la force majeure (hospitalisation, décès d'un parent ou mission de travail) est prise en compte : il faut aviser le responsable de la scolarité dans les 48 h suivant l'épreuve, avec les pièces justificatives.
    - ✔ D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « en cas d’empêchement dû à une force majeure (hospitalisation, décès d’un parent ou mission de travail), l’élève doit aviser le responsable de la scolarité dans un délai ne dépassant pas 48h à compter de la date de l’épreuve avec remise des pièces justificatives. »
  - **Claim**: Une commission désignée par la direction de l'école étudie le cas et accorde ou refuse le repassage.
    - ✔ D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « Une commission désignée par la direction de l’école étudie les différents cas et peut accorder ou refuser le repassage de l’examen. »
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-03 — absences · regime `alternance` · pair `P-absence` · **CHANGED**
- **Question**: Je suis en alternance et j'étais malade le jour d'un examen, j'ai qu'un certificat du médecin. Je fais comment ?
- **expected_article**: `D1-003/8/Absences des examens`
  - **Claim**: En cas de force majeure (hospitalisation, décès d'un parent ou mission de travail), l'alternant avise le responsable de la scolarité dans les 48 h suivant l'épreuve, avec les pièces justificatives.
    - ✔ D1-003 (official) · `D1-003/8/Absences des examens` · p.7: « en cas d’empêchement dû à une force majeure (hospitalisation, décès d’un parent ou mission de travail), l’alternant doit aviser le responsable de la scolarité dans un délai ne dépassant pas 48h à compter de la date de l’épreuve avec remise des pièces justificatives. »
  - **Claim**: Un simple certificat médical peut ne pas être accepté.
    - ✔ D1-003 (official) · `D1-003/8/Absences des examens` · p.7: « un simple certificat médical peut ne pas être considéré comme un motif valable »
  - **Claim**: Une commission désignée par la direction de l'école étudie le cas et accorde ou refuse le repassage.
    - ✔ D1-003 (official) · `D1-003/8/Absences des examens` · p.7: « Une commission désignée par la direction de l’école étudie les différents cas et peut accorder ou refuser le repassage de l’examen. »
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-04 — grading · regime `jour` · **CHANGED**
- **Question**: En cours du jour, il me faut combien de crédits pour être admis en année supérieure dès la session principale ?
- **expected_article**: `D1-001/7-5/Conditions de passage en année supérieure`
  - **Claim**: 60 ECTS acquis pour l'année en cours.
    - ✔ D1-001 (official) · `D1-001/7-5/Conditions de passage en année supérieure` · p.7: « Le nombre d’ECTS acquis pour l’année en cours doit être égal à 60 ECTS. »
  - **Claim**: Une moyenne générale d'au moins 10/20.
    - ✔ D1-001 (official) · `D1-001/7-5/Conditions de passage en année supérieure` · p.7: « La moyenne générale doit être supérieure ou égale à 10/20. »
  - **Claim**: Aucun ECTS antérieur non validé.
    - ✔ D1-001 (official) · `D1-001/7-5/Conditions de passage en année supérieure` · p.7: « Le nombre d’ECTS antérieurs cumulés non validés doit être nul. »
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-05 — retakes · regime `soir` · pair `P-passage` · **CHANGED**
- **Question**: cours du soir : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?
- **expected_article**: `D1-002/7-5/Conditions de passage en année supérieure`
  - **Claim**: Après le rattrapage : moyenne générale ≥ 10/20 et déficit cumulé ≤ 10 ECTS (0 ECTS en 4e année).
    - ✔ D1-002 (official) · `D1-002/7-5/Conditions de passage en année supérieure` · p.6: « Session: Rattrapage; Conditions d'admission: • Moyenne générale >= 10/20 • Déficit cumulé <= 10 ECTS (Il doit être égal à 0 ECTS si l'élève est en 4ème année) »
  - **Claim**: Sinon, le cas est soumis au Conseil annuel pour délibération.
    - ✔ D1-002 (official) · `D1-002/7-5/Conditions de passage en année supérieure` · p.7: « sont considérés comme des cas spécifiques qui seront soumis au « Conseil Annuel » pour délibération »
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-06 — retakes · regime `alternance` · pair `P-passage` · **CHANGED**
- **Question**: Alternance : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?
- **expected_article**: `D1-003/7-6/Conditions de passage en année supérieure`
  - **Claim**: Moyenne générale ≥ 10/20.
    - ✔ D1-003 (official) · `D1-003/7-6/Conditions de passage en année supérieure` · p.5: « La moyenne générale doit être supérieure ou égale à 10/20. »
  - **Claim**: Au plus 12 ECTS antérieurs non validés.
    - ✔ D1-003 (official) · `D1-003/7-6/Conditions de passage en année supérieure` · p.6: « Le nombre d’ECTS antérieurs cumulés non validés doit être inférieur ou égal à 12. »
  - **Claim**: 0 ECTS de déficit si l'élève est en 4e année.
    - ✔ D1-003 (official) · `D1-003/7-6/Conditions de passage en année supérieure` · p.5: « Déficit cumulé <= 12 ECTS (Il doit être égal à 0 ECTS si l'élève est en 4ème année) »
  - **Claim**: Sinon, l'élève est déclaré redoublant.
    - ✔ D1-003 (official) · `D1-003/7-6/Conditions de passage en année supérieure` · p.6: « n’ayant pas satisfait les conditions précitées d’admission en année supérieure seront déclaré redoublants »
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-07 — absences · regime `jour` · pair `P-assiduite` · **CHANGED**
- **Question**: j'ai raté 2 jours de cours pour raison médicale (cours du jour), j'ai combien de temps pour envoyer mon justificatif ?
- **expected_article**: `D1-001/9/Assiduité`
  - **Claim**: Une semaine au maximum, au service de la scolarité.
    - ✔ D1-001 (official) · `D1-001/9/Assiduité` · p.13: « l’élève doit adresser au service de scolarité un justificatif d’absence, dans un délai maximal d’une semaine. »
- Max consecutive words shared with the sources: 1
- [ ] OK  [ ] fix: ____

### T1-08 — absences · regime `soir` · pair `P-assiduite` · **CHANGED**
- **Question**: cours du soir : j'ai raté 2 jours de cours pour raison médicale, j'ai combien de temps pour envoyer mon justificatif ?
- **expected_article**: `D1-002/9/Assiduité`
  - **Claim**: Au plus tard le lendemain du début de l'empêchement : certificat médical ou justificatif au service de scolarité.
    - ✔ D1-002 (official) · `D1-002/9/Assiduité` · p.9: « l’élève doit adresser au Service de Scolarité un certificat médical ou un justificatif, au plus tard le lendemain du début de l’empêchement. »
  - **Claim**: Au-delà de 3 absences non justifiées dans un module : avertissement.
    - ✔ D1-002 (official) · `D1-002/9/Assiduité` · p.9: « Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève. »
- Max consecutive words shared with the sources: 1
- [ ] OK  [ ] fix: ____

### T1-09 — retakes · regime `alternance`
- **Question**: En alternance on a le droit de redoubler combien de fois ?
- **expected_article**: `D1-003/7-7/Redoublement`
  - **Claim**: Une seule fois sur les quatre années de la scolarité.
    - ✔ D1-003 (official) · `D1-003/7-7/Redoublement` · p.6: « Le redoublement est autorisé une seule fois au cours des quatre années de la scolarité. »
- Max consecutive words shared with the sources: 1
- [ ] OK  [ ] fix: ____

### T1-10 — internships · regime `jour` · **CHANGED**
- **Question**: Le stage d'immersion, c'est combien de semaines minimum et combien de crédits ?
- **expected_article**: `D1-001/7-9/Stage`
  - **Claim**: 6 semaines minimum et 3 ECTS.
    - ✔ D1-001 (official) · `D1-001/7-9/Stage` · p.11: « Stage: Stage d'immersion en entreprise; Nombre d'ECTS: 3; Durée minimale: 6 semaines »
  - **Claim**: Pendant l'été de la 3e année (1re année du cycle ingénieur).
    - ✔ D1-001 (official) · `D1-001/7-9/Stage` · p.11: « Période: durant l'été de la 3ème année (1ère année cycle ingénieur) »
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-11 — discipline · regime `jour` · **multi-source** · **CHANGED**
- **Question**: Cours du jour : si je me fais choper en train de tricher pendant un exam, ça se passe comment et je risque quoi ?
- **expected_article**: `D1-001/10/Honnêteté intellectuelle|D1-001/7-8/Déroulement des épreuves`
  - **Claim**: Le surveillant récupère les outils de fraude et les annexe au procès-verbal.
    - ✔ D1-001 (official) · `D1-001/10/Honnêteté intellectuelle` · p.14: « le surveillant est tenu de récupérer les outils qui ont servi à la falsification et les annexer au procès-verbal »
  - **Claim**: Un rapport de fraude est déposé auprès du chef de département de la scolarité.
    - ✔ D1-001 (official) · `D1-001/10/Honnêteté intellectuelle` · p.14: « Un rapport de fraude est déposé auprès du chef de département de la scolarité »
  - **Claim**: La fraude peut conduire l'étudiant devant le conseil de discipline.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « peut conduire son auteur devant le conseil de discipline »
  - **Claim**: Sanctions possibles : avertissement, blâme, interdiction d'une ou deux sessions d'examen, privation du rachat, privation de la mobilité internationale, exclusion d'un an au maximum, interdiction provisoire d'inscription de deux ans au maximum, exclusion définitive.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Les sanctions peuvent être sous forme d’avertissement, de blâme, d'interdiction de participation à une ou deux des sessions d'examen, de privation du rachat, de privation de la mobilité internationale, d’exclusion de l'école pour une période d'une année universitaire au maximum, d'interdiction provisoire d’inscription à l'établissement pour une période de deux années universitaires au maximum ou de l'exclusion définitive de l'école. »
- Max consecutive words shared with the sources: 1
- [ ] OK  [ ] fix: ____

### T1-12 — discipline · regime `soir` · **multi-source** · **CHANGED**
- **Question**: En cours du soir, si un prof trouve du plagiat dans mon rapport, j'aurai quelle note et quelles sanctions je risque ?
- **expected_article**: `D1-002/10/Honnêteté intellectuelle|D1-002/12/Comparution devant le conseil de discipline`
  - **Claim**: 0/20 à l'UE.
    - ✔ D1-002 (official) · `D1-002/10/Honnêteté intellectuelle` · p.10: « Lorsqu’un plagiat est constaté, la note de 0/20 est attribuée à l’UE. »
  - **Claim**: Un rapport est adressé au directeur, qui peut réunir le conseil de discipline.
    - ✔ D1-002 (official) · `D1-002/10/Honnêteté intellectuelle` · p.10: « Un rapport est adressé au directeur de l’école qui peut réunir le conseil de discipline pour décider de la sanction à adresser au plagiaire. »
  - **Claim**: Sanctions possibles : avertissement, blâme, interdiction des examens d'une ou deux sessions, renvoi d'un an au maximum, renvoi définitif.
    - ✔ D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « 1. Avertissement »
    - ✔ D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « 2. Blâme »
    - ✔ D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « 3. Interdiction de passer les examens d’une ou deux sessions »
    - ✔ D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « 4. Renvoi de l’école pour une période maximale d’une année universitaire »
    - ✔ D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « 5. Renvoi définitif de l’École »
  - **Claim**: Pas de remboursement des frais de scolarité dans les deux derniers cas.
    - ✔ D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « Dans les deux derniers cas, l’élève n’a pas le droit au remboursement des frais de scolarité. »
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-13 — grading · regime `soir` · **multi-source** · **CHANGED**
- **Question**: cours du soir: je trouve ma note d'écrit trop basse, jusqu'à quand je peux demander une double correction et quelle note sera gardée ?
- **expected_article**: `D1-002/7-2/Evaluation des élèves|D1-008/6/Note retenue`
  - **Claim**: Dans la semaine qui suit l'affichage de la note, auprès du service examen (règlement officiel du cours du soir).
    - ✔ D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « L’étudiant peut déposer une demande de double correction d’une épreuve écrite auprès de service examen dans un délai d’une semaine après l’affichage de la note de cette épreuve. »
  - **Claim**: Note retenue : la moyenne des deux corrections.
    - ✔ D1-008 (FICTITIOUS) · `D1-008/6/Note retenue` · p.1: « La note finale est la moyenne des deux corrections. »
  - **Claim**: Troisième correction si l'écart dépasse 3 points sur 20.
    - ✔ D1-008 (FICTITIOUS) · `D1-008/6/Note retenue` · p.1: « Si l'écart entre les deux notes dépasse 3 points sur 20, une troisième correction est effectuée »
  - *(note)* Source FICTIVE : à présenter comme non officielle (règle de précédence A2).
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-14 — registration · regime `soir`
- **Question**: Cours du soir : on est en décembre, je peux encore demander un report d'inscription ?
- **expected_article**: `D1-002/3/Inscription des élèves`
  - **Claim**: Non : aucune demande de report n'est recevable après le 30 novembre.
    - ✔ D1-002 (official) · `D1-002/3/Inscription des élèves` · p.3: « Aucune demande de report d'inscription n'est recevable après le 30 novembre. »
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-15 — registration · regime `alternance` · **CHANGED**
- **Question**: Si mon contrat avec l'entreprise s'arrête, je peux continuer la formation en alternance ?
- **expected_article**: `D1-003/4/Exclusion du Parcours Alternance`
  - **Claim**: Non : la rupture du contrat de travail entraîne l'exclusion automatique de la formation.
    - ✔ D1-003 (official) · `D1-003/4/Exclusion du Parcours Alternance` · p.2: « La rupture du contrat de travail, quelle qu'en soit la raison (démission, résiliation ou autre), entraîne l'exclusion automatique de la formation à ESPRIT. »
  - **Claim**: La réintégration dépend de l'avis de l'entreprise, de la décision du conseil de discipline avec l'accord de la direction des études, et du remboursement des frais engagés.
    - ✔ D1-003 (official) · `D1-003/4/Exclusion du Parcours Alternance` · p.2: « 1- L'avis de l'entreprise partenaire »
    - ✔ D1-003 (official) · `D1-003/4/Exclusion du Parcours Alternance` · p.2: « 2- La décision du conseil de discipline et l'accord de la direction des études »
    - ✔ D1-003 (official) · `D1-003/4/Exclusion du Parcours Alternance` · p.2: « 3- Le remboursement de tous les frais engagés durant son parcours de formation en alternance. »
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-16 — retakes · regime `alternance` · **CHANGED**
- **Question**: en alternance, les UE qui sont que du TP, on peut les rattraper ?
- **expected_article**: `D1-003/5/Organisation des études`
  - **Claim**: Non : les UE organisées uniquement en TP ou travaux personnalisés n'ont pas d'examen final et ne sont pas rattrapables.
    - ✔ D1-003 (official) · `D1-003/5/Organisation des études` · p.3: « Les UEs qui sont organisées exclusivement sous forme de travaux pratiques ou de travaux personnalisés n’ont pas d’examen final et ne peuvent pas faire l’objet de rattrapage. »
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-17 — campus life · regime `all` · **multi-source** · **CHANGED**
- **Question**: je suis super stressé avec les exams, il y a quelqu'un à qui parler à l'école ?
- **expected_article**: `D1-001/12/Charte de l’étudiante et de l’étudiant Espritiens|D1-003/12/Charte de l’étudiante et de l’étudiant Espritiens`
  - **Claim**: Oui : la cellule d'écoute et d'accompagnement, espace confidentiel qui accueille, écoute, informe et oriente les élèves.
    - ✔ D1-001 (official) · `D1-001/12/Charte de l’étudiante et de l’étudiant Espritiens` · p.17: « La cellule d’écoute et d’accompagnement est un espace confidentiel qui a pour objectif d’accueillir, écouter, comprendre, informer et orienter les élèves »
    - ✔ D1-003 (official) · `D1-003/12/Charte de l’étudiante et de l’étudiant Espritiens` · p.11: « La cellule d’écoute et d’accompagnement est un espace confidentiel qui a pour objectif d’accueillir, écouter, comprendre, informer et orienter les élèves »
  - **Claim**: La démarche est volontaire.
    - ✔ D1-001 (official) · `D1-001/12/Charte de l’étudiante et de l’étudiant Espritiens` · p.17: « cette démarche doit rester volontaire »
  - **Claim**: Domaines : scolarité, stress/anxiété, tristesse, mal-être.
    - ✔ D1-001 (official) · `D1-001/12/Charte de l’étudiante et de l’étudiant Espritiens` · p.17: « (scolarité, stress/anxiété, tristesse, mal être diffus…) »
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-18 — exams · regime `all` · **multi-source** · **CHANGED**
- **Question**: J'ai besoin d'un aménagement pour les examens (tiers temps), je dois déposer quoi et avant quand ?
- **expected_article**: `D1-005/4/Dossier de demande|D1-001/7-8/Déroulement des épreuves`
  - **Claim**: Le dossier comprend le formulaire FORM-04, un document médical récent et une pièce d'identité.
    - ✔ D1-005 (FICTITIOUS) · `D1-005/4/Dossier de demande` · p.1: « Le dossier comprend le formulaire FORM-04, un document médical récent établi par un médecin et une pièce d'identité. »
  - **Claim**: Il est déposé à la scolarité au moins 7 jours avant le début de la session.
    - ✔ D1-005 (FICTITIOUS) · `D1-005/4/Dossier de demande` · p.1: « Il est déposé à la scolarité au moins 7 jours avant le début de la session d'examens. »
  - **Claim**: Le règlement officiel (cours du jour) prévoit seulement un dossier médical déposé au préalable à la scolarité.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.9: « sont demandés à déposer un dossier médical à la scolarité au préalable afin d’avoir le consentement »
  - *(note)* Source FICTIVE : à présenter comme non officielle (règle de précédence A2).
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-19 — registration · regime `all` · **CHANGED**
- **Question**: En combien de temps on obtient un relevé de notes ?
- **expected_article**: `D1-006/4/Comment faire la demande`
  - **Claim**: 7 jours ouvrables à partir de la publication officielle des résultats.
    - ✔ D1-006 (FICTITIOUS) · `D1-006/4/Comment faire la demande` · p.1: « relevé de notes, 7 jours ouvrables à partir de la publication officielle des résultats »
  - **Claim**: Demande au service de la scolarité avec le formulaire FORM-03 et une pièce d'identité.
    - ✔ D1-006 (FICTITIOUS) · `D1-006/4/Comment faire la demande` · p.1: « La demande se fait auprès du service de la scolarité avec le formulaire FORM-03 et une pièce d'identité »
  - *(note)* Source FICTIVE : à présenter comme non officielle (règle de précédence A2).
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-20 — internships · regime `jour` · **CHANGED**
- **Question**: Je dois signer une convention avant de commencer mon stage d'été ? et si je l'ai pas ?
- **expected_article**: `D1-010/4/Recherche du stage et convention`
  - **Claim**: Oui : une convention tripartite est signée avant le premier jour de stage et déposée au service des stages.
    - ✔ D1-010 (FICTITIOUS) · `D1-010/4/Recherche du stage et convention` · p.1: « Avant le premier jour de stage, une convention de stage tripartite (étudiant, école, organisme d'accueil) est signée par les trois parties et déposée auprès du service des stages. »
  - **Claim**: Sans convention signée, le stage n'est pas reconnu.
    - ✔ D1-010 (FICTITIOUS) · `D1-010/4/Recherche du stage et convention` · p.1: « Un stage commencé sans convention signée n'est pas reconnu par l'école. »
  - *(note)* Source FICTIVE : à présenter comme non officielle (règle de précédence A2).
- Max consecutive words shared with the sources: 2
- [ ] OK  [ ] fix: ____

### T1-21 — retakes · regime `all` · **multi-source** · **CHANGED**
- **Question**: Pour faire une demande de repassage exceptionnel, je dois apporter quels papiers ?
- **expected_article**: `D1-004/3/Dossier de demande de repassage exceptionnel|D1-001/7-8/Déroulement des épreuves`
  - **Claim**: Le formulaire FORM-01, une pièce d'identité, et le justificatif officiel original avec une copie.
    - ✔ D1-004 (FICTITIOUS) · `D1-004/3/Dossier de demande de repassage exceptionnel` · p.1: « le formulaire de demande de repassage exceptionnel (modèle FORM-01) »
    - ✔ D1-004 (FICTITIOUS) · `D1-004/3/Dossier de demande de repassage exceptionnel` · p.1: « une pièce d'identité (CIN, passeport ou carte d'étudiant) »
    - ✔ D1-004 (FICTITIOUS) · `D1-004/3/Dossier de demande de repassage exceptionnel` · p.1: « le justificatif officiel original (attestation d'hospitalisation, acte de décès, attestation de l'autorité compétente, ordre de mission pour l'alternance), accompagné d'une copie »
  - **Claim**: Le dossier est déposé auprès du service de la scolarité.
    - ✔ D1-004 (FICTITIOUS) · `D1-004/3/Dossier de demande de repassage exceptionnel` · p.1: « Le dossier est déposé auprès du service de la scolarité »
  - **Claim**: Le règlement officiel (cours du jour) dit seulement que le dossier est déposé auprès de la scolarité.
    - ✔ D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « se font suite à un dépôt de dossier auprès de la scolarité »
  - *(note)* Source FICTIVE : à présenter comme non officielle (règle de précédence A2).
- Max consecutive words shared with the sources: 4
- [ ] OK  [ ] fix: ____

### T1-22 — internships · regime `all`
- **Question**: Mon rapport de PFE doit etre rendu combien de jours avant la soutenance ?
- **expected_article**: `D1-007/4/Calendrier de dépôt`
  - **Claim**: Au plus tard 15 jours avant la soutenance.
    - ✔ D1-007 (FICTITIOUS) · `D1-007/4/Calendrier de dépôt` · p.1: « Le rapport complet est déposé au plus tard 15 jours avant la date de soutenance. »
  - **Claim**: Les règlements officiels ne fixent pas ce délai.
    - ✔ absence check in official regulations D1-001…003: {'jours avant la date de soutenance': 0, 'jours avant la soutenance': 0, 'avant la soutenance': 0}
  - *(note)* Source FICTIVE : à présenter comme non officielle (règle de précédence A2).
- Max consecutive words shared with the sources: 3
- [ ] OK  [ ] fix: ____

### T1-23 — registration · regime `jour`
- **Question**: C'est combien exactement les frais de scolarité en 4ème année cours du jour ?
- **expected_article**: `—`
  - **Claim**: Information non trouvée dans les 13 documents.
    - ✔ absence check in the 13 documents: {'dinars': 0, 'montant des frais': 0, 'tnd': 0}
  - **Claim**: Orienter vers le service financier (FIN).
    - ✔ data/tables/directory.csv · FIN.handles: « Frais de scolarité, paiements, échéanciers, remboursements, reçus de paiement »
- Max consecutive words shared with the sources: 0
- [ ] OK  [ ] fix: ____

### T1-24 — campus life · regime `all`
- **Question**: La bibliothèque est ouverte jusqu'à quelle heure le samedi ?
- **expected_article**: `—`
  - **Claim**: Information non trouvée dans les 13 documents.
    - ✔ absence check in the 13 documents: {'horaire de la bibliothèque': 0, 'bibliothèque est ouverte': 0, "horaires d'ouverture": 0}
  - **Claim**: Orienter vers la scolarité, contact général (SCO-GEN).
    - ✔ data/tables/directory.csv · SCO-GEN.handles: « Questions générales de scolarité, dossiers des étudiants, justificatifs d'absence »
- Max consecutive words shared with the sources: 0
- [ ] OK  [ ] fix: ____

### T1-25 — internships · regime `jour`
- **Question**: Je peux faire mon stage ingénieur à l'étranger ? il y a des démarches spéciales ?
- **expected_article**: `—`
  - **Claim**: Information non trouvée dans les 13 documents.
    - ✔ absence check in the 13 documents: {'étranger': 0, "stage à l'international": 0}
  - **Claim**: Orienter vers le département des stages (STAGE) et la mobilité internationale (MOB).
    - ✔ data/tables/directory.csv · STAGE.handles: « Conventions de stage, attestations de stage, affectation et suivi des stages (PFE inclus) »
    - ✔ data/tables/directory.csv · MOB.handles: « Échanges internationaux, double diplôme, bourses de mobilité, démarches de départ »
- Max consecutive words shared with the sources: 0
- [ ] OK  [ ] fix: ____

