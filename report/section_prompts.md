# Ingénierie des prompts — Router et Regulations

## Méthode

Les prompts ont été évalués sur des jeux de questions enregistrés, en comparant les versions successives et leurs sorties structurées. Les résultats sont reproductibles à partir des scripts et fichiers du dépôt, sans nécessiter une nouvelle exécution du modèle.

## Router : v1 → v2

Le Router classe les demandes étudiantes vers les agents appropriés. La v1 utilisait 30 exemples *few-shot* ; la v2 adopte une sortie JSON plus compacte, 11 exemples ciblés et des règles explicites concernant le régime d'études, les données personnelles et les demandes d'envoi d'e-mails.

| Indicateur | v1 few-shot | v2 |
|---|---:|---:|
| Intentions exactement correctes | 47/57 | **52/57** |
| Similarité moyenne Jaccard | 0,85 | **0,93** |
| JSON et schéma valides | 57/57 | **57/57** |
| Régimes inventés | 0 | 1 |
| Rappel hors périmètre | 0,75 | **1,00** |
| Temps par appel | 52,8 s | **10,0 s** |

Sources : [analyse v1](../eval/agents/router_v1.md), [analyse v2](../eval/agents/router_v2.md), [scores v1](../eval/agents/router_results/scores_few.json), [scores v2](../eval/agents/router_results/scores_v2_few.json).

La v2 améliore la classification et réduit la taille des réponses. Toutefois, le temps v1 est mesuré en *wall time*, contre le temps modèle pour v2 : les durées ne constituent donc pas une comparaison strictement équivalente. Les 57 questions D5 sont synthétiques ; leurs étiquettes ont été relues une à une (revue CF-412) et une seule a été corrigée (D5-049 : « envoie un e-mail de ma part » relève de l'agent administratif, qui prépare un brouillon sans rien envoyer). Les scores ont été recalculés à partir des sorties enregistrées, sans nouvel appel au modèle. Un chevauchement entre un exemple et une question de développement a également été identifié puis corrigé après les mesures.

## Regulations : v2 → v3

L'agent Regulations répond à partir d'extraits de règlements, avec citations et possibilité d'abstention lorsque l'information est insuffisante.

| Indicateur (jeu de développement, 32 questions) | v2 | v3 (retenue) | v4 | v5 |
|---|---:|---:|---:|---:|
| Contrôles automatiques réussis | 32/32 | **32/32** | 32/32 | 28/32 |
| Réponses « information non trouvée » | 22 | **11** | 10 | 12 |
| Questions anglaises traitées en français (sur 3) | — | **0** | 3 | 2 |
| Réponses coupées par la limite de 200 tokens | 0 | **0** | 3 | 2 |
| Revue manuelle phrase par phrase | — | 25 fondées · 4 erronées · 3 « non trouvée » à tort | — | — |

Sur le jeu T1, la v3 obtient **20/22 réponses avec citations attendues** et traite correctement **3/3 cas d'information absente**.

Sources : [synthèse des exécutions](../eval/agents/regulations_results/summary.md), [résultats v2](../eval/agents/regulations_results/dev_v2.json), [résultats v3](../eval/agents/regulations_results/dev_v3.json), [résultats T1](../eval/agents/regulations_results/t1_v3.json), [changelog v3](../prompts/REGULATIONS-V3-CHANGELOG.md), [journal des versions](../prompts/P-REGULATIONS-001.md).

La v3 divise par deux les abstentions et répond par régime au lieu de s'abstenir. Le temps moyen plus élevé sur le jeu de développement (5,87 s contre 1,42 s) ne vient pas du prompt : la même v3 répond en 1,76 s en moyenne sur T1 ; la latence de l'offre gratuite de Gemini varie d'une exécution à l'autre.

Les contrôles automatiques ne suffisent pas : la [revue manuelle de la v3](../eval/agents/regulations_results/review_dev_v3.md), faite phrase par phrase contre le texte des articles, trouve 4 réponses erronées malgré 32/32 contrôles réussis : un règlement **officiel** présenté comme « procédure de démonstration », un élément ajouté à une liste, un article voisin cité à la place de la règle, et un seuil donné sans sa condition en crédits ECTS. Deux versions correctives (v4, v5) ont été mesurées sur le même jeu : elles corrigent le tutoiement et l'étiquetage, mais répondent en français à des questions anglaises et dépassent la limite de longueur. Elles n'ont pas été retenues. Les défauts de format sont désormais corrigés **dans le code** (`normalizeCitations` : une référence par crochets, mention « procédure de démonstration » uniquement après une source fictive) et un nouveau contrôle (`official_labelled_fictif`) déclenche une révision si une source officielle est présentée comme fictive. Leçon : ce qui est un format se garantit en code, pas en prompt ; un prompt se change une variable à la fois, mesuré à chaque fois.

Le jeu T1 a été exécuté une seule fois avec la v3 (option `--final`), après le choix de la version ; les versions v4 et v5 n'ont été mesurées que sur le jeu de développement.

## Limites communes

Les mesures portent sur des jeux restreints, sans démonstration de généralisation à toutes les demandes réelles. Les résultats dépendent des modèles, des exemples, des documents récupérés et des conditions d'exécution. Une revue humaine des cas ambigus reste nécessaire avant toute conclusion définitive.