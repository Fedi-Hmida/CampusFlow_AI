# Revue Phase 2 — intégration du travail de Doua et Ines (26 oct. 2026)

Votre branche `phase2_integration` est intégrée dans `main` via la branche `cf-208-integrate-phase2`. Vos commits sont
conservés tels quels (merge, pas de réécriture) ; les corrections sont dans des commits séparés `CF-208a…f`. Ce
document explique **ce qui a changé, pourquoi, et ce que vous faites ensuite**.

> Important : la mise à jour d'équipe et les règles du 25 oct. ne vous avaient pas été envoyées. Une bonne partie des
> écarts de process vient de là, pas de vous.

## 1. Ce qui était très bien
- **Doua — section RAG du rapport** : chiffres exacts (11 documents, 57 pages, ≈ 66 / 152 chunks), métriques bien
  définies, et surtout l'honnêteté : « aucun score ni avantage d'une stratégie n'est revendiqué ».
- **Doua — idée de D5** : couvrir routes, niveaux, anglais, cas adverses (injection, envoi d'e-mail, montants) est
  exactement la bonne démarche.
- **Ines — bibliothèque de prompts** : 7 agents, règles communes justes (régime, priorité officiel > FICTIF, `null`,
  photo = donnée), et une **vraie itération mesurée** Vision v1 → v2 (`regime` valide 2/8 → 8/8). C'est ce que le
  critère « prompt engineering » (20 %) récompense.
- **Ines — photos T4** : réalistes, toutes marquées « DOCUMENT FICTIF », cas utiles (salle masquée, injection par post-it,
  report, changement de salle, emploi du temps).

## 2. Ce qui a été corrigé, et pourquoi
| Problème | Correction | Où |
|---|---|---|
| 3 liens cassés dans `report/section_rag.md` (dossiers déplacés par CF-116) | liens corrigés + le validateur vérifie maintenant tous les liens Markdown | CF-208a |
| D5 cite un **second jeu de données jamais importé** (nouveaux D1-002/D1-003, guides finance et mobilité, calendrier avec salles) | D5 conservé tel quel dans `eval/candidates/`, trié par script : 44 lignes sans source approuvée, 4 en contradiction (ex. certificat médical en cours du jour, ancien délai REQ-08), 4 trop proches de T1–T5, 6 sans fait à vérifier, 3 confirmées | CF-208b |
| D5 réutilisait les IDs `T1-…/T5-…` et n'avait pas de régime | nouveaux IDs `D5-001…`, colonne `regime_in_question`, intentions Router | CF-208b |
| Vision v2 en clés françaises (`classe`, `salle`…) alors que les autres agents sont en anglais | un schéma JSON par agent, clés anglaises alignées sur les tables (`prompts/schemas/`) | CF-208c |
| Vision v2 : `type_evaluation = "Rattrapage"` (images 2 et 7), contre sa propre règle | Vision v3 puis v4 : `assessment` (DS / Examen) et `session` (Principale / Rattrapage) séparés, règle négative dans les deux sens, dates ISO, entrées d'emploi du temps, détection d'injection | CF-208c |
| 5 agents sans « échec observé (entrée) → correction → résultat » | format complet pour les 7 agents ; quand un agent n'a jamais tourné, c'est écrit (« not yet measured ») — jamais de score inventé | CF-208c |
| Composer en JSON (la convention projet dit texte) | Composer v2 en texte ; n8n calcule sources et marquage FICTIF | CF-208c |
| Bloc de code imbriqué (Markdown cassé), noms de personnes dans les noms de fichiers | archive corrigée (`prompts/archive/`), fichiers `P-<AGENT>-001.md` | CF-208c |
| Exemples Router avec codes du second jeu (ALG101, IA301…) | 30 exemples réécrits avec des modules et classes du calendrier approuvé | CF-208c |
| Photos T4 sans vérité terrain, sans image floue / tournée / hors sujet | vérité terrain lue sur chaque image (`eval/testsets/T4_photos.csv`), + T4-09 floue, T4-10 tournée, T4-11 menu | CF-208d |

**Correction d'une erreur de l'audit** : l'audit disait que l'e-mail mobilité de D5 était faux. C'est l'audit qui se
trompait : l'annuaire contient bien `mobilite-internationale@esprit.tn`.

## 3. Mesure Vision v1 / v2 / v3 (11 images, Gemini, température 0)
| Indicateur | v1 | v2 | v3 | v4 |
|---|---:|---:|---:|---:|
| Champs corrects (sur 88) | 71 | 82 | 86 | **87** |
| Valeurs fausses | 4 | 1 | 1 | 1 |
| JSON conforme au schéma | — | — | 7/11 | **10/11** |
| Entrées d'emploi du temps (T4-06 / T4-10, sur 14) | 0 / 0 | 0 / 0 | 14 / 14 | 14 / 13 |
| Injection du post-it signalée | impossible | impossible | oui | oui |

- Ta v2 améliore nettement la v1 (71 → 82) : ton itération est confirmée sur la vérité terrain.
- L'erreur « Rattrapage » de ta v2 **ne s'est pas reproduite** ici (température 0, mode JSON) : même modèle, réglages différents.
- v3 a introduit un nouveau défaut (forme de `change` / `timetable` non montrée) → corrigé en v4. Détails :
  `eval/agents/vision_v1_to_v4.md`. Une seule exécution par version : un écart d'un champ reste dans le bruit.

## 4. Ce que vous faites ensuite
**Doua**
1. Envoyer à Fedi les fichiers du second jeu (PDF finance, mobilité, nouveaux règlements, calendrier avec salles) **sans
   les modifier**. Fedi les importe selon `data/INTAKE.md` avec de **nouveaux** doc_ids (D1-012…).
2. Phase 3 : lancer T1 sur les index A et B avec `eval/retrieval/` (Hit@5, Recall@5, MRR), puis compléter ta section
   RAG avec les chiffres.
3. Après l'import : réécrire les lignes D5 devenues `supported` comme candidates de test (Fedi les coche).

**Ines**
1. Relire `eval/review/sheets/T4_review.md` avec Fedi (vérité terrain des 11 images).
2. Lire la comparaison v1 → v4 et proposer une v5 pour les 2 défauts restants (cases vides de l'emploi du temps tourné, classe mal lue sur l'image floue) (même protocole :
   `python -X utf8 eval/agents/vision_prompt_eval.py`).
3. Quand WF-3 v0 tourne : premier test du Router sur les 57 lignes « router_dev » de D5, puis Composer et Critic sur T1–T3.

## 5. Règles (rappel)
- Une branche par ticket (`cf-2xx-…`), messages de commit qui commencent par l'ID (`CF-2xx: …`).
- Une donnée n'entre dans le projet que par `data/raw/` (procédure `data/INTAKE.md`).
- Jamais de question T1–T5 dans un prompt ou un exemple (le validateur vérifie).
- Avant de pousser : `.venv\Scripts\python scripts\run_all.py` doit finir avec **0 error**.
