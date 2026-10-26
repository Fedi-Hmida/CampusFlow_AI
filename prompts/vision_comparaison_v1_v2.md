# CampusFlow AI — Comparaison Vision v1 / Vision v2

**Agent :** Vision  
**Outil :** Google AI Studio — Gemini 3.5 Flash Lite  
**Jeu d'essai :** 8 images (convocations, avis, emploi du temps)  
**Nature des mesures :** analyse des sorties JSON, sans vérification directe contre les images originales.

## 1. Objectif

Améliorer l'extraction structurée d'informations académiques et éviter de confondre le régime d'études (`jour`, `soir`, `alternance`) avec la nature de l'évaluation (`Devoir surveillé`, `Examen`, etc.).

## 2. Problème observé dans Vision v1

Sur 6 des 8 sorties, le champ `regime` contenait une désignation d'épreuve ou de session (`Devoir surveillé`, `Examen`, `Session de contrôle`) au lieu d'un régime d'études. Dans les deux autres sorties, la valeur était `null`.

## 3. Modifications de Vision v2

- Limitation de `regime` aux valeurs `jour`, `soir`, `alternance` ou `null`.
- Ajout du champ `type_evaluation`.
- Instruction explicite de distinguer régime d'études et type d'évaluation.
- Maintien des règles de non-invention et d'utilisation de `null` pour les données absentes ou illisibles.

## 4. Résultats comparatifs

| Indicateur | Vision v1 | Vision v2 |
|---|---:|---:|
| Images traitées | 8/8 | 8/8 |
| Réponses JSON syntaxiquement valides | 8/8 | 8/8 |
| `regime` conforme aux valeurs autorisées | 2/8 | 8/8 |
| Champ `type_evaluation` présent | 0/8 | 8/8 |
| Salle masquée de l'image 3 laissée à `null` | Oui | Oui |
| Extraction détaillée de chaque séance de l'emploi du temps (image 6) | Non | Non |

### Détail par image

| Image | Type de document | Observation v1 | Observation v2 |
|---|---|---|---|
| 1 | Convocation DS14 | `regime = Devoir surveillé` | `regime = null`, `type_evaluation = Devoir surveillé` |
| 2 | Convocation MATH201 | `regime = Session de contrôle` | `regime = null`, `type_evaluation = Rattrapage` |
| 3 | Convocation INF201 | `regime = Devoir surveillé`, salle masquée | `regime = null`, `type_evaluation = Devoir surveillé`, salle `null` |
| 4 | Avis de changement de salle | `regime = Devoir surveillé` | `regime = null`, `type_evaluation = Devoir surveillé` |
| 5 | Avis de report | `regime = Examen` | `regime = null`, `type_evaluation = Examen` |
| 6 | Emploi du temps | `regime = null`, résumé global | `regime = null`, `type_evaluation = null`, résumé global |
| 7 | Avis de session de contrôle | `regime = null` | `regime = null`, `type_evaluation = Rattrapage` |
| 8 | Convocation RES201 | `regime = Devoir surveillé` | `regime = null`, `type_evaluation = Devoir surveillé` |

## 5. Interprétation

**Amélioration constatée :** le taux de conformité du champ `regime` au schéma prévu passe de **2/8 (25 %) à 8/8 (100 %)**. Les huit réponses de v2 comportent également le nouveau champ `type_evaluation`.

**Limites :** la valeur `Rattrapage` dans `type_evaluation` (images 2 et 7) désigne plutôt une session qu'une nature d'épreuve ; le schéma mérite donc une clarification. L'image 6 reste résumée à l'échelle de la semaine et ne fournit pas une liste de séances. Enfin, la validité du JSON et la conformité du schéma ne prouvent pas l'exactitude visuelle : une comparaison avec les images sources reste nécessaire.

## 6. Conclusion

Vision v2 corrige le défaut de séparation entre régime d'études et type d'évaluation observé dans Vision v1. Le résultat est reproductible sur les huit sorties communiquées, mais l'extraction détaillée des emplois du temps et la distinction entre type d'épreuve et session restent des pistes d'amélioration.
