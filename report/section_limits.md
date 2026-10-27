# Limites et échecs

## Ce qui a échoué, et ce que nous en avons appris

- **Le contrôle qui rejetait une bonne réponse (27 octobre).**
  - *L’incident :* lors du test d’acceptation sur Telegram, la question « si on me surprend en train de tricher, je risque quoi ? » a reçu un renvoi vers la scolarité au lieu de la règle. La première réponse citait un document fictif sans l’annoncer, et le Critic l’a justement refusée. La révision était correcte, mais le second contrôle l’a rejetée à tort.
  - *La cause :* deux bibliothèques JavaScript embarquées dans le même nœud définissaient chacune une fonction `citations()`, et la seconde masquait la première.
  - *La correction :* reproduction exacte à partir de l’exécution enregistrée, test de régression, et un générateur qui refuse désormais deux définitions du même nom. Le test de fumée considère aussi qu’un renvoi inattendu est un échec : auparavant, une réponse de secours, valide pour le contrat, passait inaperçue.
  - *Leçon :* un chemin rarement emprunté (la révision) doit être testé explicitement.
- **La photo sans légende refusée (27 octobre, même test).**
  - *L’incident :* une convocation envoyée seule, la question suivant dans un second message, arrivait comme un message vide. Le Router la classait « hors périmètre » et Vision ne s’exécutait jamais.
  - *La correction :* une photo sans texte est désormais lue ; le bot dit ce qu’il y a lu et demande ce que l’étudiant veut savoir. Un nouveau scénario du test de fumée couvre ce cas.
- **La procédure fictive qui écrasait le règlement.** Une procédure d’absence fictive était mieux classée que les articles officiels « Assiduité ». Il a fallu un quota de 3 extraits officiels + 2 fictifs pour faire respecter la priorité du règlement (Hit@5 de 0,86 à 1,00).
- **Le modèle « de réflexion ».** Le tag `qwen3:4b` par défaut ignore la consigne de ne pas réfléchir : environ 1 450 tokens de raisonnement en anglais, en 207 s. Nous avons choisi la version Instruct 2507.
- **Le temps de calcul local.** Une architecture à cinq appels de LLM n’est pas viable sur CPU (environ 415 s), d’où l’hybride par agent (§ Multi-agent).

## Limites connues du système livré

1. **Faux « non trouvé ».** Avec le prompt Regulations v2, 22 questions sur 32 de l’ensemble de développement reçoivent « non trouvée » alors que plusieurs réponses existent dans les extraits. Le modèle est prudent, ce qui est sûr mais peu utile. La version v3 vise ce point (§ Prompts).
2. **Les contrôles ne voient pas une invention sémantique.** Le Critic vérifie les citations et les faits chiffrés (dates, heures, salles, mails, délais), pas le sens d’une phrase : une règle mal paraphrasée mais correctement citée passe (exemple identifié : T1-25).
3. **Corpus réduit.** 13 documents au lieu des 20 à 60 visés, dont 10 procédures fictives. Le calendrier réel est projeté depuis 2025-2026 sans salles ni heures de fin, d’où de nombreuses réponses « non communiquée ».
4. **Dépendance au cloud.** En mode hybride, la question et des extraits partent chez Google (offre gratuite, quota). Le mode local supprime cette dépendance mais dépasse le budget de latence (168 s pour une question réglementaire).
5. **Une seule file locale.** Ollama sert un appel à la fois sur CPU : des étudiants simultanés attendent les uns derrière les autres. Le Router (7 à 14 s) domine la latence, et le premier appel « à froid » prend environ 15 s.
6. **Démonstration sur un portable.** Le bot dépend d’un tunnel ngrok et d’une machine allumée. Une vidéo de secours est prévue pour la soutenance.
7. **Mémoire courte.**
   - *Ce qui est retenu :* seul le régime déclaré (« je suis en cours du soir ») passe d’un message à l’autre, sous une clé hachée, sans identifiant Telegram stocké.
   - *Ce qui ne l’est pas :* une photo envoyée seule, suivie de la question dans un second message, n’est pas reliée à cette question. Le bot décrit la photo et demande ce que l’étudiant veut savoir ; la question suivante est traitée sans la photo.
   - *Le régime :* il n’est jamais deviné depuis la classe ; le bot le redemande quand la règle en dépend.

## Pour aller plus loin

Avec plus de temps et de moyens :
- un GPU d’au moins 8 Go pour un mode tout-local sous le budget ;
- un Critic sémantique (vérification des implications) en complément des contrôles déterministes ;
- les règlements de l’année en cours et un calendrier avec salles ;
- une mémoire de conversation par étudiant, chiffrée et à durée limitée.
