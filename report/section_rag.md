# Base de connaissances et recherche réglementaire (RAG)

## Corpus et préparation

La base documentaire réglementaire comprend 11 documents en français, soit 57 pages et environ 121 206 caractères : trois règlements officiels (cours du jour, cours du soir et alternance) et huit procédures rédigées pour le projet, explicitement marquées **FICTITIOUS**. Les règlements ont été extraits et structurés en articles et sous-sections ; les documents fictifs portent leur avertissement dans le PDF et dans chaque unité de texte. Les métadonnées conservent notamment l’identifiant du document, le régime, le statut officiel ou fictif, la page et la clé de l’article.

Le régime est essentiel à la recherche : les règles peuvent différer entre cours du jour, cours du soir et alternance. Lorsqu’une procédure fictive contredit un règlement, le règlement officiel prévaut. La réponse doit distinguer une procédure de projet d’une règle officielle, citer le document, l’article et la page, et indiquer « non trouvé » lorsque le corpus ne permet pas de répondre plutôt que d’inventer une règle.

## Stratégies de découpage à comparer

Deux découpages sont prévus sur le même corpus :

- **Stratégie A — fenêtres de taille fixe :** environ 500 tokens par chunk avec 50 tokens de chevauchement ; estimation d’environ 66 chunks.
- **Stratégie B — unités documentaires :** un article ou une sous-section constitue une unité ; les unités dépassant 2 000 caractères sont scindées. L’estimation initiale est d’environ 152 chunks.

Ces volumes sont des estimations de la fiche du corpus, pas des résultats de comptage après indexation. Le découpage par article conserve mieux les références documentaires, mais une coupure fixe peut séparer une règle de son titre ou de son contexte. La relecture d’échantillons et la mesure de la recherche doivent donc accompagner le choix final.

## Indexation et recherche

L’architecture prévue utilise **BGE-M3** (`bge-m3:567m`, vecteurs de 1 024 dimensions) pour produire les embeddings et **Qdrant** pour stocker et retrouver les chunks. Les deux stratégies doivent être évaluées avec les mêmes questions, le même modèle d’embedding et le même protocole de recherche afin que la comparaison porte sur le découpage plutôt que sur un changement simultané de paramètres. Les métadonnées de régime et de statut documentaire doivent rester attachées aux chunks afin de permettre le filtrage et l’application de la priorité des sources officielles.

## Évaluation

Le jeu T1 contient 25 questions réglementaires vérifiées, avec des références d’articles attendues, des régimes différents et des questions auxquelles le corpus ne permet pas de répondre. Pour les questions répondables, l’évaluation prévue compare les articles attendus aux cinq premiers résultats :

- **Hit@5** : au moins un article attendu figure dans le top 5 ;
- **Recall@5** : proportion des articles attendus retrouvés dans le top 5 ;
- **MRR** : rang du premier article attendu, converti en réciproque.

Les questions non répondables doivent être examinées séparément : le système ne devrait pas présenter un résultat non pertinent comme une réponse étayée. Les erreurs observées sans RAG — définition erronée d’une session de rattrapage et réponse affirmative non fondée sur une absence à un examen — illustrent pourquoi la récupération de sources et leur citation sont nécessaires.

## État et limites

À la rédaction de cette section, le dépôt contient le corpus, le jeu T1 et le code des métriques, mais ne fournit pas encore de résultats mesurés comparant les stratégies A et B. Les index Qdrant, les classements top 5 et les scores Hit@5, Recall@5 et MRR doivent être ajoutés après l’ingestion et l’exécution de l’évaluation ; aucun score ni avantage d’une stratégie n’est donc revendiqué ici.

Le corpus est limité à 11 documents, en deçà de la recommandation de 20 à 60 documents du cours. Il couvre les textes disponibles pour le périmètre retenu, mais ne peut garantir une réponse aux questions absentes des sources. Les règlements officiels portent sur 2024-2025 ; le statut des données de calendrier projetées doit être traité séparément et ne doit pas être confondu avec une règle du corpus réglementaire.

## Références du projet

- [Fiche du corpus](../data/regs/CORPUS_CARD.md)
- [Jeu de test T1](../eval/testsets/T1_regulations.csv)
- [Définitions et auto-test des métriques](../eval/retrieval/retrieval_metrics.py)
- [Réponses de référence sans RAG](../eval/baselines/baseline_no_rag.md)
