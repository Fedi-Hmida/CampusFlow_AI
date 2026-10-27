# Évaluation multimodale — Vision v1 → v5

## Objectif et protocole

L'agent Vision extrait des informations structurées à partir de documents étudiants illustrés : type de document, module, classe, régime, session, date, horaires et salle, selon les champs applicables. L'évaluation repose sur 11 images T4, comprenant notamment des variations de lisibilité et de présentation.

Les versions successives du prompt ont été évaluées à l'aide du script [vision_prompt_eval.py](../eval/agents/vision_prompt_eval.py). Les résultats détaillés sont enregistrés dans les fichiers JSON du dépôt.

## Comparaison avant/après

| Indicateur | Vision v1 | Vision v5 |
|---|---:|---:|
| Champs correctement extraits | **71/88** | **88/88** |
| Schémas valides | **0/11** | **11/11** |

Sources : [scores v1](../eval/agents/vision_results/scores_v1.json), [scores v5](../eval/agents/vision_results/scores_v5.json), [prompt Vision](../prompts/P-VISION-001.md).

Entre v1 et v5, le nombre de champs corrects augmente de **17**, et toutes les sorties v5 satisfont les vérifications de schéma enregistrées. Les itérations intermédiaires et les erreurs rencontrées sont documentées dans [l'historique Vision](../eval/agents/vision_v1_to_v4.md) et la [comparaison initiale](../eval/agents/vision_v1_v2_comparison.md).

## Robustesse et limites

La v5 améliore la conformité des réponses structurées, mais un schéma valide ne garantit pas une lecture parfaite du document. En particulier, le cas d'emploi du temps **T4-10** présente encore une limite de rappel : **13 entrées sur 14** sont récupérées, contre **14/14** pour T4-06. Ces mesures concernent les entrées de tableau et ne doivent pas être confondues avec les 88 champs de l'évaluation principale.

Les images T4 représentent un petit jeu d'essai et ne couvrent pas toutes les conditions réelles : flou important, rotation extrême, occultation, éclairage variable ou documents inconnus. Une vérification humaine reste souhaitable pour les informations sensibles, notamment les dates, horaires et convocations.

## Conclusion

Vision v5 atteint les objectifs mesurés de conformité du JSON et d'extraction des champs sur T4. La prochaine amélioration prioritaire est la récupération exhaustive des lignes d'emplois du temps complexes, plutôt qu'une nouvelle optimisation du score global déjà atteint sur ce jeu.