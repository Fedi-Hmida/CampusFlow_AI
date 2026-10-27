# Cas d’usage et architecture

## Le problème

À ESPRIT, un étudiant qui se demande « je peux repasser l’épreuve si j’étais malade ? » doit croiser trois sources : un règlement de scolarité qui dépend de son régime (cours du jour, cours du soir, alternance), un calendrier d’examens et un annuaire des services. Les réponses informelles circulent sur les groupes de classe, souvent fausses : notre modèle local sans RAG répond « oui » sans condition à cette question, alors que le règlement du jour refuse le certificat médical comme justificatif d’une épreuve finale. **CampusFlow AI** est un assistant Telegram qui répond à ces questions **avec la source** (document, article, page), donne les dates et les contacts **exacts**, lit la photo d’une convocation ou d’un emploi du temps et prépare le brouillon d’une demande administrative. La règle du projet est simple : ne jamais inventer une règle, une date ou un contact. Quand l’information manque, l’assistant le dit et renvoie vers le bon bureau.

## Vue d’ensemble

Tout tourne en local dans Docker (réseau `campusflow-net`), avec des versions figées : **n8n 2.44.6** (orchestration), **Qdrant 1.20** (base vectorielle), **Ollama 0.40.10** (Qwen3 4B Instruct en 4 bits, embeddings `bge-m3:567m`), plus **ngrok** pour le webhook Telegram. Seuls trois agents qui rédigent du texte long ou lisent des images appellent **Gemini Flash-Lite** (offre gratuite) : Regulations, le brouillon Admin et Vision (§ Multi-agent, ADR-010). Un seul fichier, `config/agents.json`, choisit le mode (`hybrid` ou `local`), les versions de prompts et les modèles.

*Figure 1 — `diagrams/workflows_map.png` : les 10 workflows n8n du système, générés depuis leurs fichiers JSON.*

| Workflow | Rôle |
|---|---|
| `03a_wf3_telegram` | Entrée Telegram : accusé de réception immédiat, appel de l’assistant, réponse, journal |
| `03b_wf3_test` | Entrée de test (POST JSON) pour l’évaluation, publiée seulement pendant une campagne |
| `03_wf3_assistant` | Le cœur (42 nœuds) : Router → Vision / Regulations / Calendar / Admin → réponse fusionnée |
| `20_llm_call` | Tout appel de modèle : Gemini ou Ollama selon la configuration |
| `10`–`12` | Outils de recherche exacte : calendrier, annuaire, catalogue des démarches |
| `04_wf4_errors` | Workflow d’erreur : toute panne est journalisée |
| `01_wf1_index_regs`, `02_wf2_tables_check` | Indexation des règlements dans Qdrant ; contrôle des tables |

## Choix structurants

1. **Deux types de données, deux mécanismes.** Les règlements (13 documents, 61 pages) sont du texte : ils passent par le RAG (Qdrant, 168 articles). Le calendrier (1 560 lignes), l’annuaire (18 rôles) et le catalogue (24 démarches) contiennent des faits exacts : ils sont interrogés par des **outils de recherche exacte**, jamais par similarité (ADR-004). Une date ou une adresse mail ne passe donc jamais par un modèle de langage.
2. **Un cœur, deux entrées.** L’assistant est un sous-workflow sans URL publique, appelé à l’identique par Telegram et par l’entrée de test. Les tests exercent exactement le graphe de production, et rien de ce qui sert aux tests n’est exposé en permanence (ngrok rend publique toute URL publiée) (ADR-027).
3. **Code testé, workflows générés.** La logique des 30 nœuds Code vient de trois fichiers JavaScript testés (61 tests unitaires). Les workflows sont générés par script (`scripts/workflows/build_wf3.py`), si bien que le code déployé est exactement le code testé.
4. **Données honnêtes.** Chaque document ou ligne inventé pour le projet est marqué **FICTITIOUS** et l’assistant l’annonce (« donnée de démonstration »). Une salle ou une heure de fin inconnue reste vide (« non communiquée »), et le règlement officiel prime sur une procédure fictive.
5. **Vie privée.** Le journal (`logs/runs.jsonl`) ne contient ni le texte de la question ni l’identifiant Telegram. Le Router local refuse les demandes portant sur des données personnelles (notes, absences) avant tout appel au cloud.

## Reproductibilité

`scripts/run_all.py` reconstruit toutes les données, les index, les prompts et les workflows, puis lance un validateur de 254 contrôles (sources, liens, absence de secrets, étiquetage FICTITIOUS, fuites entre jeux de test). Toutes les versions sont figées dans `VERSIONS.md` : aucune image `latest`, modèles et dépendances Python épinglés.
