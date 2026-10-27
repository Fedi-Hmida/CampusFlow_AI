# Évaluation du système et performance

## Protocole et banc d'essai

L'évaluation globale de CampusFlow repose sur un banc d'essai automatisé ([run_e2e.py](../eval/e2e/run_e2e.py)) interrogeant le point d'entrée de test WF-3 ([CONTRACT.md](../eval/e2e/CONTRACT.md)) — exactement le même graphe que Telegram. Chaque réponse JSON est validée contre le schéma contractuel ([wf3_response.schema.json](../eval/e2e/wf3_response.schema.json)) avant d'être notée par des fonctions déterministes ([tests](../eval/e2e/scoring_test.py)), puis relue à la main.

Le protocole couvre quatre jeux de test :
- **T1 — Règlements** ([25 questions](../eval/testsets/T1_regulations.csv)) : 22 questions répondables exigeant la citation exacte (document et article) et 3 non répondables exigeant « non trouvé ». T1 est le jeu final : il est exécuté **une seule fois** sur la configuration figée (option `--final`), jamais utilisé pour régler le système.
- **T2 — Calendrier** ([12 questions](../eval/testsets/T2_calendar.csv)) : date, horaires et salle exacts d'après les tables.
- **T3 — Contacts et démarches** ([10 questions](../eval/testsets/T3_contacts_requests.csv)) : service compétent, e-mail de rôle, délais et pièces selon le régime.
- **T5 — Robustesse** ([6 questions](../eval/testsets/T5_adversarial.csv)) : hors périmètre, information manquante, prémisse fausse, régime non donné, injection dans une photo, demande d'envoi.

## Résultats de bout en bout (bot réel, 27 octobre)

Configuration : Router local (Qwen3 4B), Regulations v3 et Vision v5 sur Gemini Flash-Lite (mode hybride, [ADR-010](../diagrams/phase2_decisions.md)) ; 100 % des réponses conformes au contrat et 100 % des contrôles automatiques réussis sur les 53 questions.

| Jeu | Entièrement correct | Score moyen | Latence p50 / p90 (hybride) | Mode local |
|---|---:|---:|---:|---:|
| T1 — Règlements (final, une exécution) | **22 / 25** | 0,88 | 13,3 s / 18,7 s | non exécuté (≈ 170 s par question) |
| T2 — Calendrier | 9 / 12 → **12 / 12** après correction | 0,875 → 1,00 | 12,5 s / 14,5 s | 12 / 12 · 11,3 s / 13,4 s |
| T3 — Contacts et démarches | **3 / 10** | 0,70 | 10,1 s / 13,8 s | 3 / 10 · 9,7 s / 116,5 s |
| T5 — Robustesse | **6 / 6** | 1,00 | 9,1 s / 12,0 s | — |

Sources : [T1](../eval/e2e/results_T1_hybrid.json), [T2](../eval/e2e/results_T2_hybrid.json) (avant correction : [T2](../eval/e2e/results_T2_hybrid_before_cf409.json)), [T3](../eval/e2e/results_T3_hybrid.json), [T5](../eval/e2e/results_T5_hybrid.json), [T2 local](../eval/e2e/results_T2_local.json), [T3 local](../eval/e2e/results_T3_local.json) ; revues manuelles [T1](../eval/review/sheets/e2e_T1_review.md) et [T5](../eval/review/sheets/e2e_T5_review.md).

**Ce que montrent les échecs.**
- **T1 :** les 22 réponses correctes ont été relues phrase par phrase : aucune information inventée, les citations sont exactes, et la question où la v2 inventait une règle (T1-25) reçoit désormais « non trouvée ». Les 3 échecs viennent tous du **Router**, pas de la recherche : le stress est orienté vers le bureau des examens, une demande d'aménagement aboutit à « service introuvable », et les horaires de la bibliothèque déclenchent une demande de module et de classe.
- **T2 :** la première exécution a révélé un vrai défaut. Le Router local **inventait la session « Rattrapage »** sur 4 questions qui ne la mentionnaient pas, d'où « pas encore publiée » pour des examens présents au calendrier. Comme pour le régime, la session n'est désormais retenue que si l'étudiant l'écrit (règle en code, testée), et la réexécution donne 12 / 12. T2 n'étant pas le jeu final, cette correction est légitime ; les deux exécutions sont publiées.
- **T3 :** le bon service est trouvé 7 fois sur 10, mais le bot donne souvent **le contact sans la démarche** (pièces, délai) ou ne reconnaît pas une formulation (« reporter mon inscription », « partir en échange », remonter une réclamation). C'est une limite de couverture du catalogue et du routage, et non du modèle : le mode local fait exactement les mêmes erreurs.
- **T5 :** les 6 comportements attendus sont obtenus. En particulier, le texte d'injection lu sur la photo est signalé et ignoré, et le bot ne prétend jamais avoir envoyé un message.

**Latence.** En hybride, toutes les questions répondent sous le budget de 90 s (p90 ≤ 18,7 s). En local, les outils restent rapides (calendrier p90 13,4 s), mais une réponse qui passe par le règlement atteint 116 à 148 s : c'est la mesure de bout en bout qui confirme le choix hybride (décision prise sur le budget par composant : réponse réglementaire [114 s](../eval/latency/budget.md) en local contre [14 s](../eval/latency/budget.md) en hybride).

## Un banc d'essai doit lui-même être testé

La revue d'intégration a trouvé 12 défauts de notation et 2 défauts de fonctionnement dans la première version, tous corrigés avec un test construit à partir de la vraie réponse mal jugée. Dans les deux sens :
- **Notes trop indulgentes :** l'article « 7 » acceptait « 7-8 » ; le mot « aucun » valait « non trouvé » ; une mention de la cafétéria valait refus ; deux adresses e-mail codées en dur étaient fausses ; la question T5-05 était envoyée sans sa photo.
- **Notes trop sévères :** une date au format JJ/MM/AAAA ou « 48h » au lieu de « 48 h » n'étaient pas reconnues ; une réponse « non trouvée » qui cite la source expliquant pourquoi était refusée.
- **Défauts du banc lui-même :** en mode simulateur, les requêtes partaient vers le vrai n8n dès qu'il tournait ; la vérification du point d'entrée envoyait une requête vide au vrai bot.

Les chiffres ci-dessus sont ceux de la notation corrigée. La relecture humaine des 25 réponses T1 et des 6 réponses T5 confirme chaque verdict.

## Limites méthodologiques

1. **Exécution unique :** un seul passage par question, sans répétition ; la latence de Gemini (offre gratuite) varie fortement d'une exécution à l'autre.
2. **Taille des jeux :** 53 questions rédigées par l'équipe ; T1 a été vu une fois par le prompt Regulations v3 avant la campagne (exécution isolée, sans réglage ensuite).
3. **Contrainte matérielle :** processeur portable à 4 cœurs, sans GPU ; T1 n'a pas été exécuté en mode local (environ 70 min).
4. **Corpus synthétique :** 10 documents fictifs sur les 13 du corpus ([CORPUS_CARD.md](../data/regs/CORPUS_CARD.md)).
5. **Calendrier prévisionnel :** [1 542 dates projetées](../data/tables/exam_calendar.csv) sans salle ni heure de fin.
6. **Notation par mots-clés pour T3 et T5 :** elle est complétée par une relecture humaine, mais reste sensible aux formulations.
