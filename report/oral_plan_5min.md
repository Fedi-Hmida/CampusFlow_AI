# Plan de soutenance orale (5 minutes) — RAG & Évaluation

**Intervenante :** Doua Omrani  
**Périmètre :** Base de connaissances, stratégie RAG, banc d'essai et résultats d'évaluation  
**Durée stricte :** 5 minutes (300 secondes)

---

## 1. Découpage du temps

| Partie | Contenu | Diapositive | Durée |
|---|---|:---:|:---:|
| **Partie 1** | Problématique documentaire et architecture RAG | Slide 1 & 2 | 2 min 00 s |
| **Partie 2** | Banc d'essai automatisé et arbitrage Hybride vs Local | Slide 3 & 4 | 2 min 00 s |
| **Partie 3** | Limites méthodologiques et conclusion | Slide 5 | 1 min 00 s |

---

## 2. Diapositives et messages clés (1 diapositive = 1 minute = 1 message clé)

### Slide 1 (0:00 – 1:00) — Le défi réglementaire : concilier l'officiel et le fictif
- **Contenu :** Corpus de 13 documents ([CORPUS_CARD.md](../data/regs/CORPUS_CARD.md)), 3 règlements officiels par régime et 10 procédures fictives étiquetées ; règle absolue « l'officiel l'emporte sur le fictif » et filtrage strict par régime de l'étudiant.
- **Message clé :** *« Pas de réponse sans source : priorité stricte aux textes officiels et refus d'inventer face aux lacunes documentaires. »*

### Slide 2 (1:00 – 2:00) — Découpage documentaire : A (fixe) vs B (par article)
- **Contenu :** Comparaison sur T1 ([results_T1.md](../eval/retrieval/results_T1.md), [results_T1.json](../eval/retrieval/results_T1.json)) ; la stratégie A (77 fenêtres) transmet 8 843 caractères contre 4 145 pour la stratégie B (168 articles). Avec le quota « officiel d'abord » (3 officiels + 2 fictifs), la stratégie B atteint **Hit@5 = 1,00** et **Recall@5 = 0,93**.
- **Message clé :** *« Le découpage par article (B) divise le texte par deux et garantit 100 % de rappel des articles attendus grâce au quota officiel d'abord. »*

### Slide 3 (2:00 – 3:00) — Le banc d'essai e2e : automatisation et contrats stricts
- **Contenu :** Banc d'essai déterministe ([run_e2e.py](../eval/e2e/run_e2e.py)) et simulateur contractuel ([stub_wf3.py](../eval/e2e/stub_wf3.py)) ; 53 questions scellées (T1 à T5) vérifiées à 100 % contre les schémas JSON ([wf3_response.schema.json](../eval/e2e/wf3_response.schema.json)) et filtrées par le Critic automatique.
- **Message clé :** *« Une commande unique évalue l'assistant de bout en bout avec validation de schéma et notation objective sans complaisance. »*

### Slide 4 (3:00 – 4:00) — Latence CPU et décision d'architecture (ADR-010)
- **Contenu :** Modèle local Qwen3 4B limité à 4,13 tokens/s en génération sur CPU ([README.md](../eval/latency/README.md)) $\rightarrow$ 113,5 s pour un RAG local ; adoption du mode hybride ([budget.md](../eval/latency/budget.md)) avec Router/outils/checks en local et rédaction sur Gemini Flash-Lite $\rightarrow$ **14,3 s**, sous la cible NFR-01 de 90 s.
- **Message clé :** *« Le mode hybride préserve la confidentialité des données personnelles en local tout en divisant la latence par 8 pour rester sous les 90 secondes. »*

### Slide 5 (4:00 – 5:00) — Limites et intégrité scientifique
- **Contenu :** Transparence sur les limites réelles : petit échantillon (53 questions), exécution unique, dépendance à un calendrier projeté ([exam_calendar.csv](../data/tables/exam_calendar.csv)) et 10 documents fictifs. Évaluation complète en conditions réelles du bot notée en attente (*not measured*).
- **Message clé :** *« Une démarche d'ingénieur rigoureuse : mesurer les composants réels, tracer chaque chiffre vers un fichier et expliciter chaque limite. »*

---

## 3. Trois questions probables du jury et réponses en une ligne

1. **Question :** Pourquoi ne pas utiliser un simple seuil de similarité cosinus pour décider automatiquement si une réponse est « non trouvée » ?  
   **Réponse :** Les scores cosinus des questions répondables (dès 0,55) et non répondables (jusqu'à 0,62) se chevauchent dans Qdrant ; c'est le LLM qui doit conclure à l'absence d'information à partir des extraits fournis ([results_T1.md](../eval/retrieval/results_T1.md)).

2. **Question :** Pourquoi avoir choisi le mode hybride avec Gemini plutôt que d'optimiser le modèle local sur machine ?  
   **Réponse :** Sur processeur portable standard (4 cœurs), le débit de génération plafonne à 4,13 tokens/s ([README.md](../eval/latency/README.md)), rendant impossible le respect du budget de 90 s sans déporter la rédaction longue vers Gemini Flash-Lite ([budget.md](../eval/latency/budget.md)).

3. **Question :** Comment le système évite-t-il qu'une procédure fictive inventée prenne le pas sur le règlement officiel d'ESPRIT ?  
   **Réponse :** Chaque document fictif est explicitement étiqueté dans ses métadonnées et son texte, et la recherche B impose un quota obligatoire de 3 chunks officiels pour 2 fictifs ([CORPUS_CARD.md](../data/regs/CORPUS_CARD.md), [results_T1.md](../eval/retrieval/results_T1.md)).
