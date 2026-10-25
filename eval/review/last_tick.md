# Last tick — fixed rows only (25 Oct 2026)

Tick `[x] OK` or write `fix:`.

## Fix 1 — C4 (the PDF was right; the sheet was stale: `build_consistency_review.py` had not been re-run after the C4 update)

### C4 — discipline / sanctions (conflict)
- **Fictitious, as delivered** (D1-011 raw · p.2): « Les sanctions possibles sont : avertissement, blâme, interdiction de passer les examens d'une ou deux sessions, renvoi de l'école pour une durée maximale d'une année universitaire, renvoi définitif. Dans les deux derniers cas, l'élève n'a pas droit au remboursement des frais de scolarité. »
- **Official** (D1-001 · `D1-001/7-8/Déroulement des épreuves` · p.10): « Les sanctions peuvent être sous forme d’avertissement, de blâme, d'interdiction de participation à une ou deux des sessions d'examen, de privation du rachat, de privation de la mobilité internationale »
- **Official** (D1-002 · `D1-002/12/Comparution devant le conseil de discipline` · p.10): « Dans les deux derniers cas, l’élève n’a pas le droit au remboursement des frais de scolarité. »
- **Official** (D1-003 · `D1-003/12/Discipline` · p.8): « En aucune circonstance, l’usage de la violence physique comme verbale ne saurait être toléré. »
- **Official** (D1-003 · `D1-003/11/GESTION DES FRAUDES` · p.8): « décidera de la sanction à prendre qui peut aller jusqu’à l’exclusion de l’école »
- **Why**: The fictitious 'all regimes' list copies the evening list; the day list is longer (rachat, mobility, 2-year registration ban) and the non-refund rule is only in the evening regulation. Fedi's fix: also cite the work-study regulation (D1-003 art. 12 Discipline has no sanctions list; art. 11 sets the fraud sanction).
- **Corrected text (now in the regenerated PDF, D1-011 · `D1-011/9/Sanctions disciplinaires` · p.2)**: « Les sanctions possibles sont fixées par le règlement de scolarité du régime de l'étudiant : cours du jour (règlement du cours du jour, article 7-8, gestion des fraudes) et cours du soir (règlement du cours du soir, article 12). Alternance : le règlement de l'alternance (article 12, Discipline) impose le respect mutuel et interdit toute violence, sans fixer de liste de sanctions ; en cas de fraude, le conseil de discipline décide de la sanction, qui peut aller jusqu'à l'exclusion de l'école (article 11). Le non-remboursement des frais de scolarité en cas de renvoi est prévu par le règlement du cours du soir. »
- [ ] OK  [ ] fix: ____

## Fix 2 — REQ-11 (C3 wording for day students)

### REQ-11 — Vérification de copie · regime `all` · handler `EXA`
- source_ref: D1-002/7-2/Evaluation des élèves | D1-003/7-2/Evaluation des alternant | D1-008/4/Comment déposer la demande | D1-008/5/Traitement de la demande
- source: règlement officiel (D1-002, D1-003) ; FICTITIOUS procedure (D1-008) ; values aligned with the cited articles (CF-108)
- required_documents: « Demande écrite (matière - session - date) ; Carte étudiant » → « Demande écrite sur le formulaire FORM-02 (nom, prénom, classe, numéro d'étudiant, module, date de l'épreuve, note affichée, motif) ; pièce d'identité si demandée »
- deadline_rule: « 3 jours ouvrables après la publication des résultats » → « Cours du soir et alternance : une semaine après l'affichage de la note, auprès du service examen ; cours du jour : le règlement ne prévoit pas la double correction, l'étudiant se renseigne auprès du service examen »
- processing_time: « 5 jours ouvrables » → « 10 jours ouvrables après le dépôt de la demande (délai indicatif) »
- evidence D1-002 · `D1-002/7-2/Evaluation des élèves` · p.5: « dans un délai d’une semaine après l’affichage de la note de cette épreuve »
- evidence D1-008 · `D1-008/4/Comment déposer la demande` · p.1: « Le formulaire à utiliser est le modèle FORM-02 »
- evidence D1-008 · `D1-008/5/Traitement de la demande` · p.1: « Délai de traitement indicatif : 10 jours ouvrables après le dépôt de la demande. »
- evidence D1-008 · `D1-008/2/Principe de la double correction` · p.1: « Le règlement du cours du jour ne la mentionne pas : l'étudiant du cours du jour se renseigne auprès du service examen. »
- note: CONFLICT fixed: delivered '3 jours ouvrables' contradicts the 1-week rule of soir/alternance; documents and processing time aligned with D1-008 (two FICTITIOUS versions removed).
- [ ] OK  [ ] fix: ____

## Fix 3 — REQ-14 (D1-010 lists no documents → catalogue documents labelled FICTITIOUS (catalogue only))

### REQ-14 — Convention de stage · regime `jour` · handler `STAGE`
- source_ref: D1-010/4/Recherche du stage et convention
- source: FICTITIOUS — procedure D1-010 ; values aligned with the cited articles (CF-108) ; FICTITIOUS (catalogue only): required_documents, processing_time (D1-010 lists no documents)
- deadline_rule: « Au moins 15 jours ouvrables avant le début du stage » → « Convention tripartite signée par les trois parties avant le premier jour de stage et déposée au service des stages »
- evidence D1-010 · `D1-010/4/Recherche du stage et convention` · p.1: « Avant le premier jour de stage, une convention de stage tripartite (étudiant, école, organisme d'accueil) est signée par les trois parties et déposée auprès du service des stages. »
- note: Two FICTITIOUS versions removed: aligned with D1-010 art. 4 (delivered: 'au moins 15 jours ouvrables avant le début du stage').
- [ ] OK  [ ] fix: ____

## Fix 4 — REQ-07-SA (stale note replaced)

### REQ-07-SA — Justification d'absence en cours, TD ou TP (cours du soir, alternance) · regime `soir;alternance` · handler `SCO-GEN`
- source_ref: D1-002/9/Assiduité | D1-003/10/Assiduité
- source: règlement officiel (D1-002, D1-003) ; values aligned with the cited articles (CF-108) ; FICTITIOUS (catalogue only): processing_time
- request_type: « Justification d'absence en cours TD ou TP » → « Justification d'absence en cours, TD ou TP (cours du soir, alternance) »
- required_documents: « Formulaire de justification d'absence ; Justificatif du motif (certificat médical ou autre) » → « Certificat médical ou justificatif adressé au service de scolarité »
- deadline_rule: « 5 jours ouvrables après la date de l'absence » → « Au plus tard le lendemain du début de l'empêchement ; au-delà de trois absences non justifiées à un module : avertissement »
- evidence D1-002 · `D1-002/9/Assiduité` · p.9: « l’élève doit adresser au Service de Scolarité un certificat médical ou un justificatif, au plus tard le lendemain du début de l’empêchement. »
- evidence D1-003 · `D1-003/10/Assiduité` · p.7: « l’élève doit adresser au Service de Scolarité un certificat médical ou un justificatif, au plus tard le lendemain du début de l’empêchement. »
- evidence D1-002 · `D1-002/9/Assiduité` · p.9: « Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève. »
- evidence D1-003 · `D1-003/10/Assiduité` · p.7: « Au-delà de trois absences non justifiées à un module, un avertissement est adressé à l’élève. »
- note: One row for both regimes: D1-002 art. 9 and D1-003 art. 10 state the same rule (quotes above).
- [ ] OK  [ ] fix: ____

## Re-run of the two-versions check (automatic, `validate_data.py`)

New rule: every duration/date in `deadline_rule` / `processing_time` must appear in the cited articles. It found:
- **REQ-08-J** cited D1-004 art. 3 but its 7-day processing time is in **art. 4** → `D1-004/4/Instruction de la demande` added to source_ref.
- **REQ-04, REQ-06, REQ-07-J, REQ-07-SA, REQ-14, REQ-15**: processing times from the delivered catalogue that no document states →
  labelled `FICTITIOUS (catalogue only): processing_time` (not a second version: no procedure states another value).
- Also considered, no conflict: REQ-12 vs D1-006 art. 5 (duplicata — D1-006 covers certificates, transcripts and diploma, not convocations);
  REQ-13 vs D1-008 art. 8 (disciplinary contestation ≠ pedagogical appeal); REQ-10 vs D1-004 art. 8 (no registration deadline in D1-004).

### REQ-08-J — Justification d'absence à une épreuve finale (cours du jour) · regime `jour` · handler `SCO-GEN`
- source_ref: D1-001/7-8/Déroulement des épreuves | D1-004/3/Dossier de demande de repassage exceptionnel | D1-004/4/Instruction de la demande
- source: règlement officiel (D1-001) ; FICTITIOUS procedure (D1-004) ; values aligned with the cited articles (CF-108)
- request_type: « Justification d'absence à une épreuve » → « Justification d'absence à une épreuve finale (cours du jour) »
- required_documents: « Formulaire de justification d'absence ; Justificatif du motif (certificat médical daté et signé) ; Copie de la convocation à l'épreuve » → « Dossier de demande de repassage exceptionnel déposé à la scolarité ; justificatif recevable uniquement pour accident, maladie contagieuse, hospitalisation ou décès d'un parent proche (un certificat médical n'est pas un justificatif) »
- deadline_rule: « 3 jours ouvrables après la date de l'épreuve » → « Aucun délai fixé par le règlement ; demande traitée au cas par cas »
- processing_time: « 5 jours ouvrables (examen du dossier) » → « 7 jours ouvrables après le dépôt d'un dossier complet (délai indicatif) »
- evidence D1-001 · `D1-001/7-8/Déroulement des épreuves` · p.10: « Les certificats médicaux ne constituent pas un justificatif d’absence. »
- evidence D1-004 · `D1-004/4/Instruction de la demande` · p.1: « Délai de réponse indicatif : 7 jours ouvrables après le dépôt d'un dossier complet. »
- note: REQ-08 split by regime (official rules differ): cours du jour — certificate not accepted, no deadline; processing time from D1-004 art. 4 (FICTITIOUS).
- [ ] OK  [ ] fix: ____

- [ ] OK (labels on REQ-04/06/07-J/07-SA/14/15)  [ ] fix: ____

## Fix 5 — T3 regime-specific expected values

- **T3-03** (soir) Cours du soir : absent à un exam pour une mission de travail, je préviens qui et avant quand ?
  → role `SCO-GEN` · email_status `delivered (unverified)`
  → documents: Pièces justificatives de force majeure (hospitalisation, décès d'un parent, mission de travail) ; un simple certificat médical n'est pas un motif valable
  → deadline: Aviser le responsable de la scolarité dans un délai ne dépassant pas 48 h à compter de la date de l'épreuve
  - [ ] OK  [ ] fix: ____
- **T3-05** (jour) Je veux reporter mon inscription (cours du jour) : c'est jusqu'à quand et je dépose où ?
  → role `SCO-GEN` · email_status `delivered (unverified)`
  → documents: Formulaire de demande de report rempli et déposé au bureau d'ordre de l'école
  → deadline: Au plus tard le 30 novembre de l'année en cours pour bénéficier du remboursement ; un seul report sur toute la scolarité
  - [ ] OK  [ ] fix: ____
- **T3-10** (soir) Cours du soir : je veux une double correction de mon examen écrit, où et avant quand ?
  → role `EXA` · email_status `delivered (unverified)`
  → documents: Demande écrite sur le formulaire FORM-02 (nom, prénom, classe, numéro d'étudiant, module, date de l'épreuve, note affichée, motif) ; pièce d'identité si demandée
  → deadline: Une semaine après l'affichage de la note, auprès du service examen
  - [ ] OK  [ ] fix: ____

All other T3 rows already contained no clause of another regime (new validator check: PASS).

## Fix 6 — reproducible FICTIF PDFs

ReportLab invariant mode: two consecutive builds → **8/8 byte-identical** (SHA-256 shown in the chat).

