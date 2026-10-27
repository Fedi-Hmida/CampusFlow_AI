# Évaluation du système et performance

## Protocole et banc d'essai

L'évaluation globale de CampusFlow repose sur un banc d'essai automatisé ([run_e2e.py](../eval/e2e/run_e2e.py)) interrogeant le point d'entrée de test WF-3 ([CONTRACT.md](../eval/e2e/CONTRACT.md)). Chaque réponse JSON est validée contre le schéma contractuel ([wf3_response.schema.json](../eval/e2e/wf3_response.schema.json)) avant d'être soumise aux fonctions de notation déterministes.

Le protocole couvre quatre jeux de test scellés :
- **T1 — Règlements** ([25 questions](../eval/testsets/T1_regulations.csv)) : 22 questions répondables exigeant la citation exacte (document et article) et 3 non répondables exigeant un refus explicite.
- **T2 — Calendrier** ([12 questions](../eval/testsets/T2_calendar.csv)) : exactitude des dates, horaires et salles d'épreuves d'après les tables.
- **T3 — Contacts et démarches** ([10 questions](../eval/testsets/T3_contacts_requests.csv)) : service compétent, e-mail de rôle, délais et pièces justificatives selon le régime.
- **T5 — Robustesse** ([6 questions](../eval/testsets/T5_adversarial.csv)) : résistance aux injections, refus du hors-périmètre, correction des prémisses et brouillon sans envoi autonome.

## Comparaison hybride vs local

L'architecture supporte deux modes commutables par configuration ([agents.json](../config/agents.json), décision [ADR-010](../diagrams/phase2_decisions.md)). Le mode local exécute tous les modules sur le modèle Qwen3 4B via Ollama. Le mode hybride délègue les trois agents de rédaction longue (Regulations, Admin et Composer) à Gemini Flash-Lite via l'API, en conservant le Router, les outils tabulaires, la recherche vectorielle et les contrôles en local.

Le tableau ci-dessous compare la latence mesurée par flux utilisateur face au budget de 90 secondes ([NFR-01](../eval/latency/budget.md)), ainsi que les précisions observées :

| Flux utilisateur | Mode hybride (latence) | Mode local (latence) | Statut NFR-01 (≤ 90 s) | Précision mesurée |
|---|---:|---:|:---:|:---:|
| Question réglementaire (RAG) | [14,3 s](../eval/latency/budget.md) | [113,5 s](../eval/latency/budget.md) | Conforme en hybride (+24 s hors budget en local) | Hit@5 [1,00](../eval/retrieval/results_T1.md) (RAG B) |
| Calendrier d'examens (outil) | [8,5 s](../eval/latency/budget.md) | [11,1 s](../eval/latency/budget.md) | Conforme (deux modes) | [12 / 12](../eval/agents/tools_test.md) (tests outils) |
| Contact et démarches | [9,5 s](../eval/latency/budget.md) | [12,1 s](../eval/latency/budget.md) | Conforme (deux modes) | [18 rôles](../data/tables/directory.csv) vérifiés |
| Demande avec brouillon d'e-mail | [15,1 s](../eval/latency/budget.md) | [59,7 s](../eval/latency/budget.md) | Conforme (deux modes) | not measured (e2e bot) |
| Multi-sujets (règle + date + contact) | [21,9 s](../eval/latency/budget.md) | [182,6 s](../eval/latency/budget.md) | Conforme en hybride (2× trop lent en local) | not measured (e2e bot) |

Sur CPU portable (4 cœurs), le modèle local lit à [30,7 tokens/s](../eval/latency/README.md) et génère à [4,13 tokens/s](../eval/latency/README.md). En local, une question réglementaire dépasse le budget ([113,5 s](../eval/latency/budget.md) contre 90 s visées), alors que l'hybride répond en [14,3 s](../eval/latency/budget.md). Le Router v2 optimisé atteint [51 / 57](../eval/agents/router_v2.md) en [10,0 s](../eval/agents/router_v2.md) grâce au cache de préfixe. L'évaluation de bout en bout sur le bot complet n'a pas été mesurée (not measured : endpoint inaccessible lors de la campagne) ; le banc d'essai a été validé sur simulateur ([results_T1_stub.json](../eval/e2e/results_T1_stub.json)).

## Limites méthodologiques

Cinq limites encadrent ces résultats :
1. **Exécution unique :** mesures issues d'un passage unique sans réplicats stochastiques.
2. **Taille des jeux :** 53 questions rédigées manuellement sur l'ensemble T1 à T5.
3. **Contrainte matérielle :** exécution locale sur CPU portable 4 cœurs sans accélération GPU.
4. **Corpus synthétique :** 10 documents fictifs sur les 13 du corpus ([CORPUS_CARD.md](../data/regs/CORPUS_CARD.md)).
5. **Calendrier prévisionnel :** [1 542 dates projetées](../data/tables/exam_calendar.csv) sans salle ni heure de fin communiquée.
