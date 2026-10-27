# Architecture multi-agent

## Le patron : orchestrateur–travailleurs

Nous avons retenu un patron **orchestrateur–travailleurs** (ADR-005). Un **Router** lit le message et décide quels spécialistes travaillent. Chaque spécialiste ne connaît que sa source et ses outils, puis une fusion assemble la réponse et un contrôle (le **Critic**) l’autorise, la fait réviser une fois ou la remplace par un renvoi vers le bon bureau.

Trois alternatives ont été écartées :
- **Un agent unique avec tous les outils :** prompt long, mauvais choix d’outil, difficile à tester. Notre modèle local de 4 milliards de paramètres le supporte mal.
- **Une hiérarchie autonome :** plus d’appels, donc plus de latence sur CPU, et des chemins difficiles à déboguer.
- **Une chaîne séquentielle fixe :** elle appelle des agents inutiles (par exemple le règlement pour une simple date).

Le principe directeur est de mettre **un workflow là où les étapes sont fixes et un agent là où il faut juger**.

## Les agents

| Agent | Rôle | Moteur | Sortie | Évidence |
|---|---|---|---|---|
| **Router** | Intentions (règlement, calendrier, administratif, hors périmètre), entités (module, classe, session, régime), injection | Qwen3 4B local, 11 exemples, schéma JSON | JSON | 52/57 intentions exactes, 57/57 JSON valides, 10 s par appel |
| **Vision** | Lit une convocation, un emploi du temps ou une affiche | Gemini Flash-Lite, prompt v4 | JSON | 87/88 champs corrects sur 11 photos (T4) |
| **Regulations** | Répond à partir de 5 articles (3 officiels + 2 fictifs, filtrés par régime) avec citation | Gemini Flash-Lite, prompt v2 | Texte cité | Hit@5 = 1,00 sur T1 (§ RAG) |
| **Calendar** | Date, heure et salle exactes | Outil `10_tool_lookup_exam`, sans LLM | Ligne de table | 12/12 lignes T2 identiques |
| **Admin** | Démarche, pièces, délai, bureau ; brouillon de message si demandé | Outils 11–12 + Gemini pour le brouillon | Texte | 31 tests sur les outils |
| **Composer** | Fusionne les sections Règle / Créneau / Démarche / Photo | Code déterministe | Texte | aucun fait nouveau possible |
| **Critic** | Contrôles : citation présente et réellement récupérée ; dates, heures, salles, mails et délais présents dans les sources ; fictif annoncé ; jamais « j’ai envoyé » | Code déterministe (`checks.js`) | pass / échecs | 12 tests, moins de 50 ms ; révision réussie observée en production |

Le parcours d’une question suit ces règles :
- Une **salutation ou une commande** (« Bonjour », `/aide`, `/reset`) reçoit une réponse immédiate (0,3 s), sans LLM.
- Une question **hors périmètre** s’arrête au Router : refus poli, avec un renvoi vers la scolarité seulement pour une demande sur le dossier personnel.
- Une **photo** passe d’abord par Vision : ses faits enrichissent la recherche. Si le calendrier ne connaît pas l’épreuve, les faits lus sur la photo sont montrés, annoncés comme tels.
- Une **photo sans texte** n’est jamais refusée : le bot dit ce qu’il y a lu et demande ce que l’étudiant veut savoir.
- Une question **multi-sujets** (« double correction : quelle règle et à qui j’écris ? ») active Regulations **et** Admin, puis la fusion produit une réponse en deux sections.
- Si le Critic échoue, l’agent **révise une seule fois** en recevant la liste exacte des échecs. Si la révision échoue encore, l’assistant envoie un renvoi vers la scolarité plutôt qu’une réponse non vérifiée.

## Ce que les mesures ont changé (ADR-010)

Le plan initial prévoyait cinq appels au modèle local, Composer et Critic compris. Mesuré sur le portable de référence (i5-1135G7, sans GPU utilisable), Qwen3 4B produit 4,1 tokens/s : une réponse réglementaire prend **103 s** en local, et une requête à cinq appels environ **415 s**, très loin de notre budget de 90 s. Nous avons donc fait trois changements :

1. **Hybride par agent.** Les trois agents qui rédigent ou lisent des images passent sur Gemini Flash-Lite (réponse réglementaire en 1 à 9 s). Router, embeddings, outils et contrôles restent en local. Seuls le texte de la question et des extraits publics ou fictifs quittent la machine, jamais d’identifiant.
2. **Critic et Composer déterministes.** Un Critic LLM aurait coûté environ 70 s sur CPU. Les contrôles déterministes vérifient en quelques millisecondes ce qu’un juge LLM vérifierait le moins bien : qu’une date ou une adresse figure réellement dans les sources. La fusion déterministe garde la structure du Composer v2 sans pouvoir ajouter de fait.
3. **Router accéléré.** Le préfixe statique du Router (prompt et exemples, environ 1 250 tokens) reste dans le cache d’Ollama et la sortie a été compactée : on passe de 52,8 s à **10 s** par appel.

Résultat sur le bot réel (test de fumée, 9 scénarios, deux campagnes le 27 octobre) : **6 à 40 s** par question en mode hybride. Le Router local prend 5 à 14 s ; le temps de Gemini varie fortement d’une campagne à l’autre (réponse réglementaire de 1 à 24 s sur l’offre gratuite). En mode tout-local, une question réglementaire prend 168 s. Le mode local reste disponible d’un seul paramètre, pour la confidentialité ou en cas de quota épuisé.

## Robustesse

- **Accusé de réception immédiat :** « je cherche… » est envoyé dans la seconde.
- **Appels réseau :** chaque appel est relancé jusqu’à 3 fois.
- **Pannes :** une branche d’erreur dans chaque entrée envoie un message aimable, et le workflow WF-4 journalise toute panne non gérée (testé par une erreur forcée).
- **Boucle bornée :** une seule révision.
- **Injection :** les tentatives (« ignore tes règles… ») sont détectées par le Router et refusées. Un texte d’instruction lu sur une photo est signalé et ignoré.
