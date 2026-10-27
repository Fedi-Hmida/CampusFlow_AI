# Ingénierie des prompts — Router et Regulations

## Méthode

Les prompts ont été évalués sur des jeux de questions enregistrés, en comparant les versions successives et leurs sorties structurées. Les résultats sont reproductibles à partir des scripts et fichiers du dépôt, sans nécessiter une nouvelle exécution du modèle.

## Router : v1 → v2

Le Router classe les demandes étudiantes vers les agents appropriés. La v1 utilisait 30 exemples *few-shot* ; la v2 adopte une sortie JSON plus compacte, 11 exemples ciblés et des règles explicites concernant le régime d'études, les données personnelles et les demandes d'envoi d'e-mails.

| Indicateur | v1 few-shot | v2 |
|---|---:|---:|
| Intentions exactement correctes | 46/57 | **51/57** |
| Similarité moyenne Jaccard | 0,83 | **0,91** |
| JSON et schéma valides | 57/57 | **57/57** |
| Régimes inventés | 0 | 1 |
| Rappel hors périmètre | 0,60 | **0,80** |
| Temps par appel | 52,8 s | **10,0 s** |

Sources : [analyse v1](../eval/agents/router_v1.md), [analyse v2](../eval/agents/router_v2.md), [scores v1](../eval/agents/router_results/scores_few.json), [scores v2](../eval/agents/router_results/scores_v2_few.json).

La v2 améliore la classification et réduit la taille des réponses. Toutefois, le temps v1 est mesuré en *wall time*, contre le temps modèle pour v2 : les durées ne constituent donc pas une comparaison strictement équivalente. Les 57 questions D5 sont synthétiques et leurs étiquettes nécessitent encore une validation humaine. Un chevauchement entre un exemple et une question de développement a également été identifié puis corrigé après les mesures.

## Regulations : v2 → v3

L'agent Regulations répond à partir d'extraits de règlements, avec citations et possibilité d'abstention lorsque l'information est insuffisante.

| Indicateur | v2 | v3 |
|---|---:|---:|
| Questions de développement | 32 | 32 |
| Contrôles automatiques réussis | **32/32** | **32/32** |
| Réponses « information non trouvée » | 22 | **11** |
| Temps moyen | 1,42 s | 5,87 s |

Sur le jeu T1, la v3 obtient **20/22 réponses avec citations attendues** et traite correctement **3/3 cas d'information absente**.

Sources : [synthèse des exécutions](../eval/agents/regulations_results/summary.md), [résultats v2](../eval/agents/regulations_results/dev_v2.json), [résultats v3](../eval/agents/regulations_results/dev_v3.json), [résultats T1](../eval/agents/regulations_results/t1_v3.json), [changelog v3](../prompts/REGULATIONS-V3-CHANGELOG.md).

La v3 réduit les abstentions, au prix d'un temps moyen plus élevé. Les contrôles automatiques ne prouvent pas à eux seuls que chaque phrase est fidèle aux sources : les [revues v2](../eval/agents/regulations_results/review_dev_v2.md) et [v3](../eval/agents/regulations_results/review_dev_v3.md) doivent être complétées pour conclure sur la qualité factuelle.

## Limites communes

Les mesures portent sur des jeux restreints, sans démonstration de généralisation à toutes les demandes réelles. Les résultats dépendent des modèles, des exemples, des documents récupérés et des conditions d'exécution. Une revue humaine des cas ambigus reste nécessaire avant toute conclusion définitive.