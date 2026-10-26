# Base de connaissances et recherche réglementaire (RAG)

## Corpus et préparation

La base documentaire réglementaire comprend 13 documents en français, soit 61 pages et environ 127 766 caractères : trois règlements officiels (cours du jour, cours du soir et alternance) et dix procédures rédigées pour le projet, explicitement marquées **FICTITIOUS** (dont deux guides, frais de scolarité et mobilité internationale, ajoutés le 26 octobre faute du second jeu de données). Les règlements ont été extraits et structurés en articles et sous-sections ; les documents fictifs portent leur avertissement dans le PDF et dans chaque unité de texte. Les métadonnées conservent notamment l’identifiant du document, le régime, le statut officiel ou fictif, la page et la clé de l’article.

Le régime est essentiel à la recherche : les règles peuvent différer entre cours du jour, cours du soir et alternance. Lorsqu’une procédure fictive contredit un règlement, le règlement officiel prévaut. La réponse doit distinguer une procédure de projet d’une règle officielle, citer le document, l’article et la page, et indiquer « non trouvé » lorsque le corpus ne permet pas de répondre plutôt que d’inventer une règle.

## Stratégies de découpage à comparer

Deux découpages sont prévus sur le même corpus :

- **Stratégie A — fenêtres de taille fixe :** 2 000 caractères (≈ 500 tokens) avec 200 caractères (≈ 50 tokens) de chevauchement : **77 chunks**.
- **Stratégie B — unités documentaires :** un article ou une sous-section constitue une unité ; les unités dépassant 2 000 caractères sont scindées en fin de phrase, avec le titre de l’article répété : **168 chunks**.

Ces volumes sont comptés par le script `scripts/index/build_chunks.py` et vérifiés dans Qdrant après indexation. Le découpage par article conserve mieux les références documentaires, mais une coupure fixe peut séparer une règle de son titre ou de son contexte. La relecture d’échantillons et la mesure de la recherche doivent donc accompagner le choix final.

## Indexation et recherche

L’architecture prévue utilise **BGE-M3** (`bge-m3:567m`, vecteurs de 1 024 dimensions) pour produire les embeddings et **Qdrant** pour stocker et retrouver les chunks. Les deux stratégies doivent être évaluées avec les mêmes questions, le même modèle d’embedding et le même protocole de recherche afin que la comparaison porte sur le découpage plutôt que sur un changement simultané de paramètres. Les métadonnées de régime et de statut documentaire doivent rester attachées aux chunks afin de permettre le filtrage et l’application de la priorité des sources officielles.

## Évaluation

Le jeu T1 contient 25 questions réglementaires vérifiées, avec des références d’articles attendues, des régimes différents et des questions auxquelles le corpus ne permet pas de répondre. Pour les questions répondables, l’évaluation prévue compare les articles attendus aux cinq premiers résultats :

- **Hit@5** : au moins un article attendu figure dans le top 5 ;
- **Recall@5** : proportion des articles attendus retrouvés dans le top 5 ;
- **MRR** : rang du premier article attendu, converti en réciproque.

Les questions non répondables doivent être examinées séparément : le système ne devrait pas présenter un résultat non pertinent comme une réponse étayée. Les erreurs observées sans RAG — définition erronée d’une session de rattrapage et réponse affirmative non fondée sur une absence à un examen — illustrent pourquoi la récupération de sources et leur citation sont nécessaires.

## Résultats (T1, 22 questions répondables, 26 octobre)

Les deux index ont été remplis par le workflow WF-1 (77 et 168 points, vérifiés un à un). Les métriques sont calculées au niveau du chunk (k compte les chunks transmis à l’agent), avec le filtre de régime de la question :

| Stratégie | Hit@5 | Recall@5 | MRR | Hit@3 | Texte transmis (top 5) |
|---|---:|---:|---:|---:|---:|
| A — fenêtres fixes | 0,86 | 0,82 | 0,65 | 0,77 | 8 843 car. |
| B — articles | 0,86 | 0,75 | 0,61 | 0,86 | 4 145 car. |
| B — officiel d’abord (3 officiels + 2 fictifs) | **1,00** | **0,93** | 0,63 | 0,82 | 5 297 car. |

- À Hit@5 égal, **B transmet deux fois moins de texte** que A : sur notre processeur (≈ 31 tokens/s en lecture), c’est environ une minute de moins par question.
- Le filtre de régime compte : sans lui, A tombe à Hit@5 = 0,77.
- **Analyse des échecs :** les trois questions manquées (T1-02, T1-07, T1-08) portent sur les absences. La procédure fictive D1-004, rédigée avec les mots des étudiants et valable pour tous les régimes, passe devant l’article officiel (« Assiduité »). Réserver trois places aux textes officiels du régime corrige ces trois cas (Hit@5 = 1,00) et applique la règle « l’officiel prévaut sur le fictif ».
- **Décision :** stratégie B avec récupération « officiel d’abord » (3 + 2).
- **« Non trouvé » :** les meilleurs scores des questions sans réponse (jusqu’à 0,62) recouvrent ceux des questions répondables (dès 0,55). Aucun seuil de similarité ne peut donc décider seul ; c’est l’agent Regulations qui conclut « information non trouvée » à partir des extraits.

## Limites

Ces chiffres viennent d’une seule exécution sur 22 questions, et le choix « officiel d’abord » a été fait sur ce même jeu T1 : ils sont donc légèrement optimistes. Ils seront confirmés par les réponses complètes du bot (phase 4).

Le corpus est limité à 13 documents, en deçà de la recommandation de 20 à 60 documents du cours. Il couvre les textes disponibles pour le périmètre retenu, mais ne peut garantir une réponse aux questions absentes des sources. Les règlements officiels portent sur 2024-2025 ; le statut des données de calendrier projetées doit être traité séparément et ne doit pas être confondu avec une règle du corpus réglementaire.

## Références du projet

- [Fiche du corpus](../data/regs/CORPUS_CARD.md)
- [Jeu de test T1](../eval/testsets/T1_regulations.csv)
- [Définitions et auto-test des métriques](../eval/retrieval/retrieval_metrics.py)
- [Réponses de référence sans RAG](../eval/baselines/baseline_no_rag.md)
- [Résultats détaillés T1 (A / B)](../eval/retrieval/results_T1.md) · [Journal d’indexation](../eval/retrieval/ingestion_log.md)
