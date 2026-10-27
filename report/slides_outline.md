# Plan des slides — Phase 3 : prompts et multimodal

## Slide 1 — Objectif de la Phase 3
- Fiabiliser le routage, les réponses réglementaires et la lecture de documents.
- Méthode : prompts versionnés, jeux de tests, sorties enregistrées et comparaisons avant/après.

## Slide 2 — Router v1 → v2
- Intentions exactes : **46/57 → 51/57**.
- Jaccard : **0,83 → 0,91**.
- Sortie compacte et 11 exemples ciblés au lieu de 30.
- Limites : étiquettes D5 non validées ; temps mesurés différemment.
- Preuve : [router_v2.md](../eval/agents/router_v2.md).

## Slide 3 — Regulations v2 → v3
- Abstentions sur développement : **22 → 11** ; contrôles automatiques **32/32**.
- T1 (exécuté une fois) : **20/22** citations attendues ; **3/3** abstentions justifiées.
- Revue manuelle : 25 réponses fondées, 4 erronées malgré les contrôles → les formats sont réparés en code.
- v4 et v5 mesurées et rejetées (langue, longueur) : un prompt se change une variable à la fois.
- Preuve : [summary.md](../eval/agents/regulations_results/summary.md).

## Slide 4 — Vision v1 → v5
- Champs corrects : **71/88 → 88/88**.
- Sorties conformes au schéma : **10/11 (v4) → 11/11 (v5)** ; cases vides sur T4-10 : **10 → 0**.
- Limite résiduelle : emploi du temps T4-10, **13/14** entrées.
- Preuves : [scores_v1.json](../eval/agents/vision_results/scores_v1.json), [scores_v5.json](../eval/agents/vision_results/scores_v5.json).

## Slide 5 — Bilan et prochaines étapes
- Progrès observés sur la classification, la réduction des abstentions et la structure des sorties Vision.
- Ne pas confondre contrôles automatiques et exactitude factuelle.
- Priorités : validation humaine D5, revue Regulations et amélioration des tableaux complexes.
- Revue d'équipe avant intégration à `main`.