# CampusFlow AI — mise à jour pour Doua et Ines (mardi 27 octobre 2026)

**À lire avant 9:00.** Ce document contient tout ce qui a changé depuis la fusion de votre travail, les décisions qui
changent votre façon de travailler, et vos tâches des jours 4 et 5. Vous ne devriez rien avoir à demander pour démarrer ;
si quelque chose manque, c'est une erreur de ce document : dites-le à Fedi à 9:00.

**Sommaire**
1. Votre travail de Phase 2 : ce qu'il est devenu
2. Ce qui a été construit depuis (lundi 26 octobre)
3. Les décisions qui changent votre façon de travailler
4. Où en est le projet
5. Vos tâches (Doua, puis Ines)
6. Démarrer : installation et commandes
7. Calendrier des jours 4 et 5
8. Règles de fusion et « fini »
9. FAQ
10. Glossaire

---

## 1. Votre travail de Phase 2 : ce qu'il est devenu (CF-208)

Votre branche `phase2_integration` est **entièrement dans `main`** ; vos commits sont gardés tels quels, les corrections
sont dans des commits séparés. Le détail, avec les retours personnels, est dans
[team/REVIEW_2026-10-26_phase2.md](REVIEW_2026-10-26_phase2.md). En bref :

| Votre livrable | Devenu | Où |
|---|---|---|
| Section RAG (Doua) | gardée, liens réparés, **complétée avec les résultats mesurés** (A vs B, décision) | `report/section_rag.md` |
| Questions D5 (Doua) | gardées telles quelles, triées par script : **57 questions servent à régler le Router** (jeu de développement) ; ce n'est pas un jeu de test | `eval/candidates/` |
| Bibliothèque de prompts (Ines) | un fichier par agent, schémas JSON en anglais, journal « échec → correction → résultat » | `prompts/P-*-001.md`, `prompts/schemas/` |
| Vision v1 → v2 (Ines) | votre itération est **confirmée sur la vérité terrain** (71 → 82 champs justes sur 88), puis v3 et v4 | `eval/agents/vision_v1_to_v4.md` |
| 8 photos T4 (Ines) | gardées + 3 images dérivées (floue, tournée, hors sujet) → **11 images avec vérité terrain** | `eval/testsets/T4_photos.csv` |

Deux corrections de l'audit, pour être juste : l'adresse `mobilite-internationale@esprit.tn` de D5 était **bonne** ; et
l'erreur « Rattrapage » de Vision v2 **ne s'est pas reproduite** avec la température 0.

---

## 2. Ce qui a été construit depuis (lundi 26 octobre)

| Ticket | Quoi | Le chiffre à retenir | Fichier de preuve |
|---|---|---|---|
| CF-117 | Le second jeu de données n'est jamais arrivé : **2 guides FICTIFS écrits pour le projet** (frais de scolarité D1-012, mobilité internationale D1-013), **sans montants** et **sans stage à l'étranger** pour ne rien inventer | corpus : **13 documents, 61 pages** | `data/regs/CORPUS_CARD.md` |
| CF-016 | Découpage des textes en morceaux (« chunks ») | A (fenêtres fixes) : **77** · B (par article) : **168** | `data/index/README.md` |
| CF-015/017 | Les deux index remplis dans Qdrant par le workflow WF-1 | 77 + 168 points, vérifiés un à un ; 5 min 28 s | `eval/retrieval/ingestion_log.md` |
| CF-018/019 | 3 outils de recherche exacte : examens, contacts, démarches | **30 tests** ; n8n = code testé sur **15/15** requêtes | `eval/agents/tools_test.md` |
| CF-020 | Évaluation de la recherche sur T1 (22 questions) | A : Hit@5 0,86 · B : Hit@5 0,86 avec **2× moins de texte** · **B « officiel d'abord » : Hit@5 1,00** | `eval/retrieval/results_T1.md` |
| CF-008b | Mesure de vitesse du modèle local (4B sur processeur) | lecture **30,7 tokens/s**, écriture **4,1 tokens/s** → chaîne complète ≈ **415 s** (objectif 90 s) | `eval/latency/README.md` |
| CF-022 | Router v1 mesuré sur les 57 questions de développement | sans exemples : 42/57 et **7 régimes inventés** ; avec 30 exemples : 46/57, **0 inventé**, mais 52,8 s | `eval/agents/router_v1.md` |
| CF-010 | La décision de latence, mesurée | Router v2 : **51/57 en 10 s** ; Regulations en local **103 s** contre **4,6–8,8 s** sur Gemini | `eval/latency/budget.md`, `eval/agents/router_v2.md` |
| CF-010 | Critic automatique (`checks.js`) : citations, dates, salles, e-mails, délais, mention FICTIF, jamais « envoyé » | 11 tests ; a attrapé **3 vrais défauts** | `workflows/lib/checks.js` |
| CF-011 | **Décision ADR-010 : mode hybride** (section 3) | question réglementaire **14 s** au lieu de 114 s | `config/agents.json` |
| CF-118 | Toutes les lignes de test vérifiées contre leurs sources | **251/251 contrôles, 0 en attente** | `eval/review/ticks/delegated_tick_2026-10-26.md` |
| CF-014/021 | Schéma d'architecture + page des décisions de Phase 2 | — | `diagrams/architecture.md`, `diagrams/phase2_decisions.md` |
| CF-400 | Tout ce qu'il faut pour que vous travailliez **sans le portable de Fedi** (section 6) | ligne de base v2 mesurée pour Ines | `eval/agents/regulations_results/summary.md` |

**Deux découvertes importantes pour le rapport :**
- La procédure FICTIVE d'absences (D1-004), écrite avec les mots des étudiants, passait **devant** les articles officiels
  « Assiduité » : 3 questions T1 manquées. Réserver 3 places aux textes officiels a tout corrigé — c'est notre règle
  « l'officiel l'emporte sur le fictif » appliquée dès la recherche.
- Les contrôles automatiques ne voient pas tout : une réponse a **inventé une règle** avec une vraie citation (T1-25 :
  « le stage ne peut pas être effectué à l'étranger » — l'article n'en parle pas). C'est une des cibles de Regulations v3.

---

## 3. Les décisions qui changent votre façon de travailler

1. **Mode hybride (ADR-010).** En local, le modèle 4B met ≈ 103 s pour écrire une réponse réglementaire ; Gemini Flash-Lite
   met quelques secondes. Donc : Router, outils, recherche et contrôles restent **en local** ; Regulations, brouillon Admin
   et Composer passent sur **Gemini**. Un seul réglage (`config/agents.json`, `"mode": "local"`) remet tout en local.
   Le rapport compare les deux modes.
2. **Ce qui sort de la machine (NFR-03 modifiée).** Seulement le texte de la question, les extraits du règlement (publics ou
   FICTIFS) et les photos — **jamais** un identifiant Telegram, un nom ou un journal. Le Router (local) refuse les
   demandes de données personnelles avant tout appel en ligne.
3. **Recherche (ADR-025).** Index B (un morceau par article), filtré par le régime de l'étudiant, **3 extraits officiels +
   2 FICTIFS**. Aucun seuil de score ne peut décider « non trouvé » : c'est l'agent Regulations qui le décide.
4. **On règle sur le jeu dev, on mesure T1 une seule fois.** T1 est le test final : interdit de régler un prompt dessus.
   Le script refuse T1 sans l'option `--final`.
5. **Une coche = vérifié contre la source.** Les lignes cochées pour Fedi portent « delegated by Fedi (26 Oct) ».
6. **Le Router v2** : le régime n'est jamais déduit de la classe ; ses propres notes / absences = hors périmètre ;
   « envoie-le à ma place » = Admin, qui prépare un brouillon et **n'envoie jamais**.
7. **Sécurité.** n8n est accessible depuis Internet (ngrok) : un webhook de test est publié **seulement pendant un essai**,
   puis dépublié. Une clé ne va **jamais** dans un fichier ni dans un commit.

---

## 4. Où en est le projet

| Phase | Avancement |
|---|---:|
| 0–3 Installation, données, base de connaissances, évaluation de la recherche | **100 %** |
| 4 Bot minimal (WF-3 v0) | 30 % — Fedi mardi matin |
| 5 Multi-agents + vision | 45 % |
| 6 Itération des prompts | 50 % |
| 7 Robustesse | 15 % |
| 8 Livraison (rapport, slides, vidéo, répétition) | 30 % |
| **Total** | **≈ 68 %** — dans les temps |

**Ce qui manque :** le bot lui-même (Fedi), son évaluation (Doua), Regulations v3 et Vision v5 (Ines), la gestion des
erreurs, le rapport, les slides et deux répétitions.

---

## 5. Vos tâches

**Qui fait quoi, en une phrase :** Fedi construit le bot, **Doua le teste**, **Ines améliore ses prompts**. Le bot vit dans
un seul n8n sur le portable de Fedi : à trois sur le même workflow, on s'écraserait. Vous avez donc chacune un travail
**à côté** du bot, sur vos propres fichiers, faisable sur votre portable, et qui porte une grosse part de la note :
évaluation (Doua), prompt engineering 20 % et multimodalité 15 % (Ines).

### Doua — tester le bot de bout en bout (≈ 8–9 h)

| Ticket | Ce que tu livres | C'est réussi quand… | Temps |
|---|---|---|---|
| **CF-411** banc d'essai | `eval/e2e/run_e2e.py` + `eval/e2e/stub_wf3.py` (un faux bot pour développer sans attendre) | une seule commande lance T1, T2, T3 et T5 sur la porte de test du bot ([eval/e2e/CONTRACT.md](../eval/e2e/CONTRACT.md)) ; chaque réponse est validée par `eval/e2e/wf3_response.schema.json` ; scores : article attendu cité, « non trouvé » juste, contrôles, valeurs exactes T2/T3, latence p50/p90 ; résultats dans `eval/e2e/results_<jeu>_<mode>.json` + feuilles de relecture manuelle (T1 : chaque phrase est-elle fondée ? T5 : bon comportement ?) ; tourne sur ton stub d'abord, puis mardi 12:30 sur le vrai bot **en hybride et en local** | 4–5 h |
| **CF-412** étiquettes D5 | `eval/candidates/D5_label_review.csv` (`d5_id, current, proposed, reason`) | les 57 lignes relues avec les règles du Router v2 (section 3, point 6), en particulier les 10 cas discutables de `eval/agents/router_v1.md` ; Fedi applique ensuite | 45 min |
| **CF-413** rapport + oral | `report/section_evaluation.md` (1 page) ; mise à jour de `report/section_rag.md` ; plan de ton oral (5 min, RAG + évaluation) | chaque chiffre renvoie à un fichier ; comparaison hybride / local ; limites écrites (une exécution, petits jeux, réglage) | mer. matin |

**Ce que j'attends de toi :** un banc d'essai **reproductible** (une commande, mêmes réglages pour les deux modes) et
**honnête** (les échecs listés, pas cachés), et une section qu'un examinateur peut vérifier ligne par ligne.
**Si tu finis avant :** prépare la fiche des 4 cas de démo (message exact à envoyer, réponse attendue, plan B).

### Ines — améliorer les prompts du bot (≈ 8–9 h)

| Ticket | Ce que tu livres | C'est réussi quand… | Temps |
|---|---|---|---|
| **CF-421** Regulations v3 | un bloc `<!-- template:v3 -->` dans `prompts/P-REGULATIONS-001.md` + une ligne du journal de versions | corrige les **4 défauts mesurés de v2** : **(1) « non trouvée » à tort quand le régime n'est pas donné** (v2 : **22/32** « non trouvée » sur le jeu dev, dont D5-016 et D5-018 alors que la réponse est dans les extraits) → donner la règle **de chaque régime** avec sa source, ou demander le régime ; **(2) règle inventée** (T1-25) ; **(3)** procédure FICTIVE non signalée ; **(4)** « non trouvée » sans contact. Mesure sur le **jeu dev** uniquement ; relecture dans `review_dev_v3.md`. **Objectif :** 0 phrase inventée, nettement moins de « non trouvée » à tort que v2, contrôles toujours à 100 %, ≤ 160 tokens | 3 h |
| **CF-422** Vision v5 | un bloc `<!-- template:v5 -->` dans `prompts/P-VISION-001.md` + journal | corrige les 2 défauts de v4 : cases vides listées sur l'emploi du temps tourné (T4-10), « 5D56 » au lieu de s'abstenir sur l'image floue (T4-09) ; mesure sur les 11 images T4 ; **pas de régression** : ≥ 87/88 champs justes, 11/11 conformes au schéma | 2 h |
| **CF-423** rapport + slides | `report/section_prompts.md` (1 p.), `report/section_multimodal.md` (1 p.), `report/slides_outline.md` | tableaux avant/après : Router v1 → v2, Vision v1 → v5, Regulations v2 → v3, chaque chiffre relié à un fichier ; limites | mer. matin |

**Ce que j'attends de toi :** des versions qui **battent une mesure**, pas des impressions, avec le journal
« échec → correction → résultat » complet ; des sections qui racontent ces itérations avec leurs chiffres.
**Si tu finis avant :** les slides complètes et le script de la vidéo de secours (2 min, les 4 cas de démo).

---

## 6. Démarrer : installation et commandes

**Récupérer le projet et créer ta branche**
```powershell
git checkout main
git pull origin main
git checkout -b cf-411-e2e-harness        # Doua (puis cf-412-d5-labels, cf-413-report-eval)
git checkout -b cf-421-regulations-v3     # Ines (puis cf-422-vision-v5, cf-423-report-prompts)
.venv\Scripts\python scripts\run_all.py   # doit finir par « 0 error »
```
Si `.venv` n'existe pas : `python -m venv .venv` puis `.venv\Scripts\python -m pip install -r requirements.txt`
(Python 3.12 ; versions figées — vérifié : un environnement neuf reconstruit tout à l'identique, 251/251). Node.js sert aux
tests des outils ; sans Node, `run_all` les saute simplement.

**Ta clé Gemini (Ines, et Doua si besoin)** — dans le terminal uniquement :
```powershell
$env:GEMINI_API_KEY="ta-clé-AI-Studio"     # PowerShell  (cmd : set GEMINI_API_KEY=ta-clé)
```
Jamais dans un fichier, jamais dans un commit, jamais dans un message.

**Ines — Regulations v3**
```powershell
# 1) écris le bloc <!-- template:v3 --> dans prompts/P-REGULATIONS-001.md (copie la v2 et corrige)
.venv\Scripts\python -X utf8 eval\agents\regulations_prompt_eval.py --version v3 --set dev --via direct --limit 5   # essai rapide
.venv\Scripts\python -X utf8 eval\agents\regulations_prompt_eval.py --version v3 --set dev --via direct             # les 32 questions
# 2) remplis eval/agents/regulations_results/review_dev_v3.md ; compare avec summary.md (v2)
```
**Ines — Vision v5**
```powershell
# bloc <!-- template:v5 --> dans prompts/P-VISION-001.md, puis :
.venv\Scripts\python -X utf8 eval\agents\vision_prompt_eval.py --versions v5 --via direct
```
**Doua — banc d'essai**
- Lis [eval/e2e/CONTRACT.md](../eval/e2e/CONTRACT.md) : question envoyée, JSON reçu, ce qu'on note.
- Écris d'abord `stub_wf3.py` (un petit serveur qui répond au format du contrat), puis `run_e2e.py` contre lui.
- Mardi 12:30, Fedi ouvre la vraie porte de test sur son portable : vous lancez les deux modes ensemble.
- Les métriques de la recherche existent déjà : `eval/retrieval/retrieval_metrics.py`.

**Fichiers utiles (déjà prêts)**
| Fichier | À quoi il sert |
|---|---|
| `eval/agents/regulations_contexts_dev.jsonl` | 32 questions de développement **avec leurs extraits** (pour régler v3) |
| `eval/agents/regulations_contexts_T1.jsonl` | les 25 questions T1 avec extraits (mesure finale, `--final`) |
| `eval/agents/regulations_results/review_dev_v2.md` | les 32 réponses de v2 à relire : ta ligne de base |
| `eval/agents/gemini_client.py` | appel Gemini (via n8n chez Fedi, ou direct avec ta clé) |
| `config/agents.json` | qui tourne où, quelle version de prompt, quels budgets |
| `eval/latency/budget.md` | temps par type de question, local vs hybride |

---

## 7. Calendrier

| Quand | Fedi | Doua | Ines |
|---|---|---|---|
| **mar. 9:00** | lancement (15 min, questions sur ce document) | | |
| mar. matin | WF-3 v0 (questions de règlement) | stub + banc d'essai | Regulations v3 |
| **mar. 12:30** | ouvre la porte de test | tests T1 sur le vrai bot (hybride + local) | Vision v5 |
| **mar. 13:30** | **point n°1** (15 min) : premiers chiffres, blocages | | |
| mar. après-midi | WF-3 v1 (les 4 cas de démo) | T2, T3, T5 ; revue D5 | fin v3 / v5 |
| **mar. 18:00** | **fusion n°1** : CF-412, CF-421, CF-422 (et CF-411 s'il est prêt) | | |
| **mer. 10:00** | **point n°2** : résultats finaux, échecs à corriger | | |
| **mer. 12:00** | **gel des fonctionnalités + fusion n°2** | section évaluation | sections prompts + multimodal |
| **mer. 14:00** | **gel du rapport** · 15:00 slides + vidéo · **16:00 et 18:00 deux répétitions complètes** | | |

---

## 8. Règles de fusion et « fini »

1. **Une branche par ticket**, créée depuis le dernier `main`.
2. Messages de commit qui commencent par l'ID : `CF-421: …`.
3. **Jamais de push sur `main`** : tu pousses ta branche (`git push origin cf-421-regulations-v3`) et tu préviens Fedi,
   qui relit et fusionne.
4. Avant de pousser : `run_all` doit finir à **0 error**.
5. Tu ne modifies **que tes fichiers** :

| Propriétaire | Fichiers |
|---|---|
| Fedi | `workflows/` (WF-1 à WF-4, `lib/`), `config/`, `scripts/`, `data/`, `report/section_architecture.md`, `section_multiagent.md`, `section_limits.md` |
| Doua | `eval/e2e/**` (sauf `CONTRACT.md` et le schéma), `eval/candidates/D5_label_review.csv`, `report/section_rag.md`, `report/section_evaluation.md` |
| Ines | `prompts/P-REGULATIONS-001.md` (bloc v3 + journal), `prompts/P-VISION-001.md` (bloc v5 + journal), `eval/agents/regulations_results/**`, `eval/agents/vision_results/v5/`, `report/section_prompts.md`, `report/section_multimodal.md`, `report/slides_outline.md` |

6. Besoin de changer autre chose (contrat, données, config) : **on demande à Fedi**.
7. Jamais de clé ni de donnée personnelle dans un fichier ; jamais une question de T1–T5 dans un prompt ou un exemple
   (le validateur le vérifie).

**« Fini » veut dire :** critères d'acceptation remplis · fichiers sur ta branche · `run_all` à 0 error · chaque chiffre
relié à un fichier · limites écrites · Fedi a relu et fusionné.

---

## 9. FAQ

- **Je n'ai pas Docker / Qdrant / n8n.** Ce n'est pas nécessaire : les extraits sont déjà exportés, et Gemini s'appelle
  avec ta propre clé (`--via direct`).
- **Je peux régler mon prompt sur T1 ?** Non : T1 est la mesure finale. Règle sur le jeu dev (D5) ; T1 est lancé une fois,
  avec `--final`, mercredi.
- **Le script dit « set the environment variable GEMINI_API_KEY ».** Ta clé n'est pas dans le terminal courant : refais
  la commande de la section 6 dans le même terminal.
- **Erreur 429.** C'est la limite gratuite de Gemini : le script attend et réessaie ; sinon, attends une minute.
- **Une réponse « non trouvée » passe tous les contrôles, est-ce normal ?** Oui : c'est pour cela que la feuille de
  relecture a une case « non trouvée à tort ». C'est le défaut principal de v2.
- **Je veux changer `checks.js`, le contrat ou la config.** Demande à Fedi : ce sont des points de contact partagés.
- **`run_all` échoue.** Copie les dernières lignes à Fedi avant de pousser quoi que ce soit.

## 10. Glossaire

| Terme | Sens |
|---|---|
| **WF-3** | le workflow n8n du bot (Telegram → agents → réponse) ; WF-1 indexe, WF-2 vérifie les tables, WF-4 gère les erreurs |
| **Router** | l'agent qui lit la question et choisit qui répond (règlement, calendrier, démarches, hors périmètre) |
| **Chunk** | morceau de texte indexé dans Qdrant ; stratégie A = fenêtres fixes, B = un article |
| **Hit@5** | la bonne source est-elle dans les 5 premiers extraits ? |
| **Officiel d'abord** | 3 extraits officiels + 2 FICTIFS, pour que l'officiel ne soit jamais écrasé |
| **Jeu dev / T1** | dev = questions pour régler (D5) ; T1 = test final vérifié, mesuré une seule fois |
| **Contrôles / Critic** | `checks.js` : vérifie citations, dates, salles, e-mails, délais, mention FICTIF, « jamais envoyé » |
| **Mode hybride / local** | hybride = rédaction longue sur Gemini (rapide) ; local = tout sur le portable (≈ 2 min par réponse) |
| **Porte de test** | `/webhook/wf3-test` : le bot répond en JSON au lieu de Telegram, pour l'évaluation |
| **Stub** | faux bot qui respecte le contrat, pour développer le banc d'essai sans attendre le vrai |
