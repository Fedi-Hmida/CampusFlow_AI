# CF-108 — Request catalogue mapping review

Each row: delivered value → catalogue value, the article keys it now cites and the evidence. Tick or fix.
Rule A2: where the delivered row contradicted an official article, the official rule was applied.

### REQ-01 — Attestation de scolarité · regime `all` · handler `SCO-LEVEL`
- source_ref: D1-006/4/Comment faire la demande
- note: Only a FICTITIOUS source (D1-006 art. 4: FORM-03 + pièce d'identité, 3 jours ouvrables) — the delivered row says e-mail + carte étudiant, 2–3 jours: two fictitious versions, kept as delivered.
- [ ] OK  [ ] fix: ____

### REQ-02 — Relevé de notes · regime `all` · handler `SCO-LEVEL`
- source_ref: D1-006/4/Comment faire la demande
- note: FICTITIOUS source only (D1-006: 7 jours ouvrables after publication).
- [ ] OK  [ ] fix: ____

### REQ-03 — Attestation de réussite · regime `all` · handler `SCO-LEVEL`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-04 — Duplicata de la carte étudiant · regime `all` · handler `SCO-LEVEL`
- source_ref: D1-011/2/Accès aux locaux
- note: D1-011 art. 2 (FICTITIOUS) says report the loss within 48 h; delivered row says 'dès la perte'. Compatible, kept.
- [ ] OK  [ ] fix: ____

### REQ-05 — Changement de classe ou de groupe · regime `all` · handler `SCO-LEVEL`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-06 — Report d'études ou congé · regime `jour;soir` · handler `SCO-GEN`
- source_ref: D1-001/3/Inscription des élèves | D1-002/3/Inscription des élèves
- handler_role_id: « SCO-LEVEL » → « SCO-GEN »
- required_documents: « Demande écrite motivée ; Justificatif (certificat médical ou autre) ; Carte étudiant » → « Formulaire de demande de report rempli et déposé au bureau d'ordre de l'école »
- deadline_rule: « À déposer avant le début du semestre concerné » → « Au plus tard le 30 novembre de l'année en cours (cours du jour : condition du remboursement ; cours du soir : aucune demande recevable après le 30 novembre) ; un seul report sur toute la scolarité »
- evidence D1-002 · `D1-002/3/Inscription des élèves` · p.3: « Aucune demande de report d'inscription n'est recevable après le 30 novembre. »
- note: CONFLICT fixed: delivered deadline 'avant le début du semestre' → official 30 November; official place = bureau d'ordre (handler set to SCO-GEN as the closest role).
- [ ] OK  [ ] fix: ____

### REQ-07-J — Justification d'absence en cours, TD ou TP (cours du jour) · regime `jour` · handler `SCO-GEN`
- source_ref: D1-001/9/Assiduité
- request_type: « Justification d'absence en cours TD ou TP » → « Justification d'absence en cours, TD ou TP (cours du jour) »
- required_documents: « Formulaire de justification d'absence ; Justificatif du motif (certificat médical ou autre) » → « Justificatif d'absence (raison médicale ou force majeure) adressé au service de scolarité »
- deadline_rule: « 5 jours ouvrables après la date de l'absence » → « Dans un délai maximal d'une semaine »
- evidence D1-001 · `D1-001/9/Assiduité` · p.13: « un justificatif d’absence, dans un délai maximal d’une semaine. »
- note: Split by regime (official rules differ).
- [ ] OK  [ ] fix: ____

### REQ-07-SA — Justification d'absence en cours, TD ou TP (cours du soir, alternance) · regime `soir;alternance` · handler `SCO-GEN`
- source_ref: D1-002/9/Assiduité | D1-003/10/Assiduité
- request_type: « Justification d'absence en cours TD ou TP » → « Justification d'absence en cours, TD ou TP (cours du soir, alternance) »
- required_documents: « Formulaire de justification d'absence ; Justificatif du motif (certificat médical ou autre) » → « Certificat médical ou justificatif adressé au service de scolarité »
- deadline_rule: « 5 jours ouvrables après la date de l'absence » → « Au plus tard le lendemain du début de l'empêchement ; au-delà de trois absences non justifiées à un module : avertissement »
- evidence D1-002 · `D1-002/9/Assiduité` · p.9: « au plus tard le lendemain du début de l’empêchement. »
- note: Split by regime (official rules differ).
- [ ] OK  [ ] fix: ____

### REQ-08-J — Justification d'absence à une épreuve finale (cours du jour) · regime `jour` · handler `SCO-GEN`
- source_ref: D1-001/7-8/Déroulement des épreuves | D1-004/3/Dossier de demande de repassage exceptionnel
- request_type: « Justification d'absence à une épreuve » → « Justification d'absence à une épreuve finale (cours du jour) »
- required_documents: « Formulaire de justification d'absence ; Justificatif du motif (certificat médical daté et signé) ; Copie de la convocation à l'épreuve » → « Dossier de demande de repassage exceptionnel déposé à la scolarité ; justificatif recevable uniquement pour accident, maladie contagieuse, hospitalisation ou décès d'un parent proche (un certificat médical n'est pas un justificatif) »
- deadline_rule: « 3 jours ouvrables après la date de l'épreuve » → « Aucun délai fixé par le règlement ; demande traitée au cas par cas »
- evidence D1-001 · `D1-001/7-8/Déroulement des épreuves` · p.10: « Les certificats médicaux ne constituent pas un justificatif d’absence. »
- note: Split by regime (official rules differ).
- [ ] OK  [ ] fix: ____

### REQ-08-SA — Justification d'absence à une épreuve (cours du soir, alternance) · regime `soir;alternance` · handler `SCO-GEN`
- source_ref: D1-002/7-2/Evaluation des élèves | D1-003/8/Absences des examens
- request_type: « Justification d'absence à une épreuve » → « Justification d'absence à une épreuve (cours du soir, alternance) »
- required_documents: « Formulaire de justification d'absence ; Justificatif du motif (certificat médical daté et signé) ; Copie de la convocation à l'épreuve » → « Pièces justificatives de force majeure (hospitalisation, décès d'un parent, mission de travail) ; un simple certificat médical n'est pas un motif valable (cours du soir) ou peut ne pas l'être (alternance) »
- deadline_rule: « 3 jours ouvrables après la date de l'épreuve » → « Aviser le responsable de la scolarité dans un délai ne dépassant pas 48 h à compter de la date de l'épreuve »
- evidence D1-002 · `D1-002/7-2/Evaluation des élèves` · p.5: « dans un délai ne dépassant pas 48h à compter de la date de l’épreuve »
- note: Split by regime (official rules differ).
- [ ] OK  [ ] fix: ____

### REQ-09 — Épreuve de remplacement · regime `all` · handler `EXA`
- source_ref: D1-001/7-8/Déroulement des épreuves | D1-002/7-2/Evaluation des élèves | D1-003/8/Absences des examens
- note: Official: the scolarité (jour) or a commission (soir/alternance) decides the retake; the delivered deadline/organisation by EXA is FICTITIOUS.
- [ ] OK  [ ] fix: ____

### REQ-10 — Inscription à la session de rattrapage · regime `all` · handler `EXA`
- source_ref: D1-001/7-6/Session de rattrapage | D1-002/7-7/Session de rattrapage
- note: Official texts give the right to retake; the 5-day registration deadline is FICTITIOUS.
- [ ] OK  [ ] fix: ____

### REQ-11 — Vérification de copie · regime `all` · handler `EXA`
- source_ref: D1-002/7-2/Evaluation des élèves | D1-003/7-2/Evaluation des alternant
- deadline_rule: « 3 jours ouvrables après la publication des résultats » → « Cours du soir et alternance : une semaine après l'affichage de la note (demande de double correction auprès du service examen) ; cours du jour : non fixé par le règlement (FICTITIOUS : 3 jours ouvrables après la publication des résultats) »
- evidence D1-002 · `D1-002/7-2/Evaluation des élèves` · p.5: « dans un délai d’une semaine après l’affichage de la note de cette épreuve »
- note: CONFLICT fixed: delivered '3 jours ouvrables' contradicts the 1-week rule of soir/alternance.
- [ ] OK  [ ] fix: ____

### REQ-12 — Duplicata de convocation · regime `all` · handler `EXA`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-13 — Recours contre une décision · regime `all` · handler `DIR-ETU`
- source_ref: FICTITIOUS — no source
- note: No source (the regulations describe discipline hearings, not a general appeal).
- [ ] OK  [ ] fix: ____

### REQ-14 — Convention de stage · regime `jour` · handler `STAGE`
- source_ref: D1-010/4/Recherche du stage et convention
- note: FICTITIOUS sources only (D1-010: convention signed before the first day).
- [ ] OK  [ ] fix: ____

### REQ-15 — Dépôt de l'attestation et des livrables de stage · regime `jour` · handler `STAGE`
- source_ref: D1-001/7-9/Stage
- request_type: « Attestation de stage » → « Dépôt de l'attestation et des livrables de stage »
- required_documents: « Convention de stage signée ; Fiche d'évaluation visée par le tuteur ; Rapport de stage déposé » → « Attestation de stage délivrée par l'entreprise d'accueil ; journal et rapport de stage (à déposer au service des stages) »
- evidence D1-001 · `D1-001/7-9/Stage` · p.10: « une attestation de stage délivrée par l’entreprise d’accueil »
- note: CONFLICT fixed: the attestation is issued by the host company (official 7-9), not by the STAGE office; the request becomes 'dépôt' of the deliverables.
- [ ] OK  [ ] fix: ____

### REQ-16 — Dépôt du sujet de PFE · regime `all` · handler `STAGE`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-17 — Candidature à la mobilité internationale · regime `all` · handler `MOB`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-18 — Demande de bourse de mobilité · regime `all` · handler `MOB`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-19 — Demande d'échéancier de paiement · regime `all` · handler `FIN`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-20 — Reçu ou attestation de paiement · regime `all` · handler `FIN`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-21 — Remboursement de frais · regime `all` · handler `FIN`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

### REQ-22 — Accompagnement carrière (CV et entretiens) · regime `all` · handler `CAREER`
- source_ref: FICTITIOUS — no source
- note: No source.
- [ ] OK  [ ] fix: ____

