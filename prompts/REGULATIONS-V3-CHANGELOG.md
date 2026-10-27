### Regulations Prompt v3 — Journal des modifications

**Problèmes identifiés (Failure)**
- Confusion entre validation d'une UE/UA, validation du semestre et passage en année supérieure.
- Réponses parfois dans la mauvaise langue.
- Références aux documents fictifs mal signalées.
- Réponses incomplètes aux questions comportant plusieurs demandes.
- Réponses parfois trop prudentes (« Information non trouvée »).

**Modifications apportées (Fix)**
- Renforcement des règles de validation et des exceptions.
- Obligation de répondre dans la langue de la question.
- Clarification du format des citations et du marquage des procédures de démonstration.
- Ajout d'instructions pour traiter chaque partie d'une question.
- Amélioration des réponses conditionnelles selon le régime d'études.

**Résultats (Result)**
- Évaluation `dev_v3` : **32/32 contrôles automatiques PASS**.
- Amélioration des réponses sur les rattrapages, les absences et les questions en anglais.
- Quelques limites sémantiques restent identifiées dans la revue manuelle, notamment D5-002, D5-012, D5-022 et D5-046.

**Décision :** conserver la version v3 actuelle et documenter les limites restantes avant le test final `t1`.
### Évaluation finale — T1

- Version évaluée : `v3`
- Jeu de test : `t1` (25 questions)
- Contrôles automatiques : **25/25 PASS (100 %)**
- Citations attendues : **20/22 (90,9 %)**
- Questions sans réponse correctement identifiées : **3/3**
- Réponses « non trouvée » incorrectes : **0**
- Temps moyen de réponse : **1,76 seconde**
- Échecs automatiques : **0**

**Conclusion :** la version v3 satisfait tous les contrôles automatiques du test final T1. Deux écarts subsistent concernant les citations attendues ; ils sont documentés comme limites de l'évaluation.