# T1 review sheet — 25 regulation questions (CF-111)

Each row: tick **OK** if the proposed answer is exactly what the quoted source says, or write the fix.
Quotes were located verbatim in `data/regs/clean/` by `scripts/build_t1.py`; article keys and pages are
derived from them (A4). FICTITIOUS sources must be presented as non-official (A2).

## Coverage

- regimes (answerable): {'jour': 7, 'soir': 6, 'alternance': 5, 'all': 4}; FICTITIOUS-sourced rows: 6; pair groups: {'P-absence': 3, 'P-passage': 2, 'P-assiduite': 2};
  two-article rows: 3; unanswerable: 3; topics: ['absences', 'campus life', 'discipline', 'exams', 'grading', 'internships', 'registration', 'retakes']
- ✅ rows == 25
- ✅ jour >= 5
- ✅ soir >= 5
- ✅ alternance >= 5
- ✅ FICTITIOUS-sourced >= 5
- ✅ regime pair groups 3-4
- ✅ two-article questions 2-3
- ✅ unanswerable == 3
- ✅ topics cover exams/retakes/absences/grading/internships/discipline/registration

## Rows

### T1-01 — absences · regime `jour` · pair `P-absence`
- **Question**: Jsuis tombé malade le jour de mon exam final (grosse migraine), j'ai un certif du médecin : ça suffit pour le repasser ?
- **Proposed answer**: Non. En cours du jour, seuls un accident, une maladie contagieuse, une hospitalisation ou le décès d'un parent proche justifient une absence à une épreuve finale ; un certificat médical ne suffit pas. L'étudiant peut déposer un dossier de repassage exceptionnel à la scolarité, traité au cas par cas.
- **Source** D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Les certificats médicaux ne constituent pas un justificatif d’absence. »
- **Source** D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Toutefois, les demandes de repassage exceptionnelles sont traitées au cas par cas »
- Max consecutive words shared with the source: 1
- [ ] OK  [ ] fix: ____

### T1-02 — absences · regime `soir` · pair `P-absence`
- **Question**: Cours du soir : j'ai loupé l'examen à cause d'une migraine et j'ai seulement un certificat médical, est-ce que ça marche ?
- **Proposed answer**: Non, un simple certificat médical n'est pas un motif valable. En cas de force majeure (hospitalisation, décès d'un parent, mission de travail), il faut aviser le responsable de la scolarité dans les 48 h suivant l'épreuve avec les justificatifs ; une commission accorde ou refuse le repassage.
- **Source** D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « Il est à noter qu’un simple certificat médical n'est pas considéré comme un motif valable. »
- **Source** D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « dans un délai ne dépassant pas 48h à compter de la date de l’épreuve »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-03 — absences · regime `alternance` · pair `P-absence`
- **Question**: Je suis en alternance et j'étais malade le jour d'un examen, j'ai qu'un certificat du médecin. Je fais comment ?
- **Proposed answer**: Aviser le responsable de la scolarité dans les 48 h suivant l'épreuve, avec les pièces justificatives. Un simple certificat médical peut ne pas être accepté (force majeure : hospitalisation, décès d'un parent, mission de travail) ; une commission décide du repassage.
- **Source** D1-003 (official) · `D1-003/8/Absences des examens` · p.7: « dans un délai ne dépassant pas 48h à compter de la date de l’épreuve avec remise des pièces justificatives »
- **Source** D1-003 (official) · `D1-003/8/Absences des examens` · p.7: « un simple certificat médical peut ne pas être considéré comme un motif valable »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-04 — grading · regime `jour`
- **Question**: En cours du jour, il me faut combien de crédits pour être admis en année supérieure dès la session principale ?
- **Proposed answer**: 60 ECTS acquis pour l'année en cours, une moyenne générale ≥ 10/20 et aucun ECTS antérieur non validé.
- **Source** D1-001 (official) · `D1-001/7-5/Conditions de passage en année supérieure` · p.7: « Le nombre d’ECTS acquis pour l’année en cours doit être égal à 60 ECTS. »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-05 — retakes · regime `soir` · pair `P-passage`
- **Question**: cours du soir : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?
- **Proposed answer**: Avec une moyenne générale ≥ 10/20 et un déficit cumulé ≤ 10 ECTS (0 ECTS en 4e année). Sinon, le dossier est soumis au Conseil annuel.
- **Source** D1-002 (official) · `D1-002/7-5/Conditions de passage en année supérieure` · p.6: « Déficit cumulé <= 10 ECTS (Il doit être égal à 0 ECTS si l'élève est en 4ème année) »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-06 — retakes · regime `alternance` · pair `P-passage`
- **Question**: Alternance : aprés le rattrapage, je peux passer en année sup avec combien d'ECTS de retard au maximum ?
- **Proposed answer**: Avec une moyenne générale ≥ 10/20 et au plus 12 ECTS antérieurs non validés (0 en 4e année d'après le tableau) ; sinon l'élève est déclaré redoublant.
- **Source** D1-003 (official) · `D1-003/7-6/Conditions de passage en année supérieure` · p.6: « Le nombre d’ECTS antérieurs cumulés non validés doit être inférieur ou égal à 12. »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-07 — absences · regime `jour` · pair `P-assiduite`
- **Question**: j'ai raté 2 jours de cours pour raison médicale (cours du jour), j'ai combien de temps pour envoyer mon justificatif ?
- **Proposed answer**: Une semaine au maximum, au service de la scolarité.
- **Source** D1-001 (official) · `D1-001/9/Assiduité` · p.13: « un justificatif d’absence, dans un délai maximal d’une semaine. »
- Max consecutive words shared with the source: 1
- [ ] OK  [ ] fix: ____

### T1-08 — absences · regime `soir` · pair `P-assiduite`
- **Question**: cours du soir : j'ai raté 2 jours de cours pour raison médicale, j'ai combien de temps pour envoyer mon justificatif ?
- **Proposed answer**: Au plus tard le lendemain du début de l'empêchement (certificat médical ou justificatif au service de scolarité). Au-delà de 3 absences non justifiées dans un module : avertissement.
- **Source** D1-002 (official) · `D1-002/9/Assiduité` · p.9: « au plus tard le lendemain du début de l’empêchement. »
- **Source** D1-002 (official) · `D1-002/9/Assiduité` · p.9: « Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève. »
- Max consecutive words shared with the source: 1
- [ ] OK  [ ] fix: ____

### T1-09 — retakes · regime `alternance`
- **Question**: En alternance on a le droit de redoubler combien de fois ?
- **Proposed answer**: Une seule fois sur les quatre années de la formation.
- **Source** D1-003 (official) · `D1-003/7-7/Redoublement` · p.6: « Le redoublement est autorisé une seule fois au cours des quatre années de la scolarité. »
- Max consecutive words shared with the source: 1
- [ ] OK  [ ] fix: ____

### T1-10 — internships · regime `jour`
- **Question**: Le stage d'immersion, c'est combien de semaines minimum et combien de crédits ?
- **Proposed answer**: 6 semaines minimum, 3 ECTS, pendant l'été de la 3e année (1re année du cycle ingénieur).
- **Source** D1-001 (official) · `D1-001/7-9/Stage` · p.11: « Stage: Stage d'immersion en entreprise; Nombre d'ECTS: 3; Durée minimale: 6 semaines »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-11 — discipline · regime `jour` · **spans two articles**
- **Question**: Cours du jour : si je me fais choper en train de tricher pendant un exam, ça se passe comment et je risque quoi ?
- **Proposed answer**: Le surveillant récupère les outils de fraude et les annexe au procès-verbal ; un rapport de fraude est transmis et l'étudiant peut être conduit devant le conseil. Sanctions possibles : avertissement, blâme, interdiction d'une ou deux sessions, privation du rachat, privation de la mobilité internationale, exclusion jusqu'à un an, interdiction d'inscription jusqu'à deux ans, exclusion définitive.
- **Source** D1-001 (official) · `D1-001/10/Honnêteté intellectuelle` · p.14: « le surveillant est tenu de récupérer les outils qui ont servi à la falsification et les annexer au procès-verbal »
- **Source** D1-001 (official) · `D1-001/7-8/Déroulement des épreuves` · p.10: « Les sanctions peuvent être sous forme d’avertissement, de blâme »
- Max consecutive words shared with the source: 1
- [ ] OK  [ ] fix: ____

### T1-12 — discipline · regime `soir` · **spans two articles**
- **Question**: En cours du soir, si un prof trouve du plagiat dans mon rapport, j'aurai quelle note et quelles sanctions je risque ?
- **Proposed answer**: 0/20 à l'UE ; un rapport est adressé au directeur, qui peut réunir le conseil de discipline : avertissement, blâme, interdiction des examens d'une ou deux sessions, renvoi jusqu'à un an, renvoi définitif (sans remboursement des frais dans les deux derniers cas).
- **Source** D1-002 (official) · `D1-002/10/Honnêteté intellectuelle` · p.10: « la note de 0/20 est attribuée à l’UE »
- **Source** D1-002 (official) · `D1-002/12/Comparution devant le conseil de discipline` · p.10: « Renvoi de l’école pour une période maximale d’une année universitaire »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-13 — grading · regime `soir` · **spans two articles**
- **Question**: cours du soir: je trouve ma note d'écrit trop basse, jusqu'à quand je peux demander une double correction et quelle note sera gardée ?
- **Proposed answer**: Dans la semaine qui suit l'affichage de la note, auprès du service examen (règlement officiel du cours du soir, art. 7-2). La note retenue (moyenne des deux corrections, 3e correction si l'écart dépasse 3 points) vient de la procédure FICTIVE D1-008 : à présenter comme non officielle.
- **Source** D1-002 (official) · `D1-002/7-2/Evaluation des élèves` · p.5: « dans un délai d’une semaine après l’affichage de la note de cette épreuve »
- **Source** D1-008 (FICTITIOUS) · `D1-008/6/Note retenue` · p.1: « La note finale est la moyenne des deux corrections. »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-14 — registration · regime `soir`
- **Question**: Cours du soir : on est en décembre, je peux encore demander un report d'inscription ?
- **Proposed answer**: Non, aucune demande de report n'est recevable après le 30 novembre.
- **Source** D1-002 (official) · `D1-002/3/Inscription des élèves` · p.3: « Aucune demande de report d'inscription n'est recevable après le 30 novembre. »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-15 — registration · regime `alternance`
- **Question**: Si mon contrat avec l'entreprise s'arrête, je peux continuer la formation en alternance ?
- **Proposed answer**: Non : la rupture du contrat de travail entraîne l'exclusion automatique de la formation. Une réintégration dépend de l'avis de l'entreprise, de la décision du conseil de discipline avec l'accord de la direction des études, et du remboursement des frais engagés.
- **Source** D1-003 (official) · `D1-003/4/Exclusion du Parcours Alternance` · p.2: « entraîne l'exclusion automatique »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-16 — retakes · regime `alternance`
- **Question**: en alternance, les UE qui sont que du TP, on peut les rattraper ?
- **Proposed answer**: Non : les UE organisées uniquement en TP ou travaux personnalisés n'ont pas d'examen final et ne sont pas rattrapables.
- **Source** D1-003 (official) · `D1-003/5/Organisation des études` · p.3: « n’ont pas d’examen final et ne peuvent pas faire l’objet de rattrapage. »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-17 — campus life · regime `jour`
- **Question**: je suis super stressé avec les exams, il y a quelqu'un à qui parler à l'école ?
- **Proposed answer**: Oui : la cellule d'écoute et d'accompagnement, espace confidentiel et volontaire qui accueille, écoute et oriente les élèves (scolarité, stress, anxiété, mal-être).
- **Source** D1-001 (official) · `D1-001/12/Charte de l’étudiante et de l’étudiant Espritiens` · p.17: « La cellule d’écoute et d’accompagnement est un espace confidentiel »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-18 — exams · regime `all`
- **Question**: J'ai besoin d'un aménagement pour les examens (tiers temps), je dois déposer quoi et avant quand ?
- **Proposed answer**: Selon la procédure FICTIVE D1-005 : formulaire FORM-04, document médical récent et pièce d'identité, déposés à la scolarité au moins 7 jours avant la session. À présenter comme non officiel ; le règlement officiel (cours du jour, art. 7-8) prévoit seulement un dossier médical déposé au préalable à la scolarité.
- **Source** D1-005 (FICTITIOUS) · `D1-005/4/Dossier de demande` · p.1: « Le dossier comprend le formulaire FORM-04, un document médical récent établi par un médecin et une pièce d'identité. »
- Max consecutive words shared with the source: 1
- [ ] OK  [ ] fix: ____

### T1-19 — registration · regime `all`
- **Question**: En combien de temps on obtient un relevé de notes ?
- **Proposed answer**: Selon la procédure FICTIVE D1-006 : 7 jours ouvrables à partir de la publication officielle des résultats, demande à la scolarité (FORM-03 + pièce d'identité). Non officiel.
- **Source** D1-006 (FICTITIOUS) · `D1-006/4/Comment faire la demande` · p.1: « relevé de notes, 7 jours ouvrables à partir de la »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-20 — internships · regime `jour`
- **Question**: Je dois signer une convention avant de commencer mon stage d'été ? et si je l'ai pas ?
- **Proposed answer**: Selon le guide FICTIF D1-010 : oui, une convention tripartite signée avant le premier jour et déposée au service des stages ; sinon le stage n'est pas reconnu. Non officiel.
- **Source** D1-010 (FICTITIOUS) · `D1-010/4/Recherche du stage et convention` · p.1: « Un stage commencé sans convention signée n'est pas reconnu par l'école. »
- Max consecutive words shared with the source: 2
- [ ] OK  [ ] fix: ____

### T1-21 — retakes · regime `all`
- **Question**: Pour faire une demande de repassage exceptionnel, je dois apporter quels papiers ?
- **Proposed answer**: Selon la procédure FICTIVE D1-004 : formulaire FORM-01, pièce d'identité, justificatif officiel original et sa copie, déposés à la scolarité. Le règlement officiel (cours du jour, art. 7-8) dit seulement que le dossier est déposé auprès de la scolarité.
- **Source** D1-004 (FICTITIOUS) · `D1-004/3/Dossier de demande de repassage exceptionnel` · p.1: « le formulaire de demande de repassage exceptionnel (modèle FORM-01) »
- Max consecutive words shared with the source: 4
- [ ] OK  [ ] fix: ____

### T1-22 — internships · regime `all`
- **Question**: Mon rapport de PFE doit etre rendu combien de jours avant la soutenance ?
- **Proposed answer**: Selon la procédure FICTIVE D1-007 : au plus tard 15 jours avant la soutenance. Les règlements officiels ne fixent pas de délai.
- **Source** D1-007 (FICTITIOUS) · `D1-007/4/Calendrier de dépôt` · p.1: « Le rapport complet est déposé au plus tard 15 jours avant la date de soutenance. »
- Max consecutive words shared with the source: 3
- [ ] OK  [ ] fix: ____

### T1-23 — registration · regime `jour`
- **Question**: C'est combien exactement les frais de scolarité en 4ème année cours du jour ?
- **Proposed answer**: Information non trouvée dans les règlements : orienter vers le service financier (FIN).
- **Unanswerable**: searched ['dinars', 'montant des frais', 'tnd'] → no match in the 11 documents.
- Max consecutive words shared with the source: 0
- [ ] OK  [ ] fix: ____

### T1-24 — campus life · regime `all`
- **Question**: La bibliothèque est ouverte jusqu'à quelle heure le samedi ?
- **Proposed answer**: Information non trouvée : orienter vers la scolarité (contact général, SCO-GEN).
- **Unanswerable**: searched ['horaire de la bibliothèque', 'bibliothèque est ouverte', "horaires d'ouverture"] → no match in the 11 documents.
- Max consecutive words shared with the source: 0
- [ ] OK  [ ] fix: ____

### T1-25 — internships · regime `jour`
- **Question**: Je peux faire mon stage ingénieur à l'étranger ? il y a des démarches spéciales ?
- **Proposed answer**: Information non trouvée dans les règlements : orienter vers le département des stages (STAGE) et la mobilité internationale (MOB).
- **Unanswerable**: searched ['étranger', "stage à l'international"] → no match in the 11 documents.
- Max consecutive words shared with the source: 0
- [ ] OK  [ ] fix: ____

