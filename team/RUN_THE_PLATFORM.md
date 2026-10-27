# Utiliser la plateforme CampusFlow AI soi-même

Pour Doua et Ines. Ce guide explique **trois façons** de tester le travail, de la plus simple à la plus complète.
Lis d'abord la section 0 : elle explique pourquoi on ne peut pas simplement « copier le bot ».

---

## 0 · Comment ça marche, en 4 phrases

1. **Le bot `@CampusFlowAI_bot` n'est pas « dans » Telegram :**
   - Telegram reçoit les messages et les renvoie à une adresse web, le **webhook**.
   - Cette adresse est le tunnel ngrok du portable de Fedi, et c'est n8n, sur ce portable, qui fabrique la réponse.
2. **N'importe qui peut écrire au bot.** Il n'est pas lié à un compte qui l'utilise : il suffit de le chercher dans Telegram. Fedi en est seulement le **propriétaire** (créé avec @BotFather).
3. **Un bot n'a qu'un seul webhook.** Si quelqu'un met le *token* du bot de Fedi dans un autre n8n, le bot part vers ce portable et le bot de démonstration ne répond plus. **Ne jamais utiliser le token de Fedi** : le script d'installation le refuse.
4. **Tout le reste est dans le dépôt :** données, prompts, workflows, scripts. Une copie complète se monte donc en une commande (niveau B). Seuls les **secrets** sont personnels : la clé Gemini, le token d'un bot, le compte ngrok.

| Niveau | Pour quoi faire | Installation | Temps |
|---|---|---|---|
| **A** · utiliser le bot de Fedi | essayer le produit comme un étudiant | rien | 1 min |
| **B** · copie locale **sans** Telegram | tester ses prompts / son banc d'essai sur sa machine, en autonomie | Docker + 1 commande | 30–45 min (le premier téléchargement) |
| **C** · copie locale **avec son propre bot** | avoir son bot Telegram à soi | B + un bot + un compte ngrok | + 15 min |

---

## Niveau A · Utiliser le bot de Fedi (aucune installation)

1. Dans Telegram, cherche **@CampusFlowAI_bot**, ouvre-le, appuie sur **Démarrer**.
2. Envoie : `C'est quand l'épreuve d'Advanced Deep Learning pour la classe 5DS6 ?`
   - **Attendu :** « Je cherche… », puis « vendredi 15/01/2027, 09:00 – 11:00, salle B12 … donnée de démonstration ».
3. Autres essais : les cas 5.1 à 5.7 de la recette (contact, hors périmètre, injection, photo, régime).

**Limites :**
- ça marche seulement si le portable de Fedi est allumé, avec Docker lancé ;
- vous n'avez pas accès à l'interface n8n de Fedi ;
- les réponses passent par la configuration **de Fedi**, donc vos prompts ne sont actifs qu'une fois fusionnés.

**Pour votre banc d'essai sur le vrai bot :** Fedi ouvre la porte de test pendant la campagne (`eval/e2e/CONTRACT.md`, « Opening the endpoint »).

---

## Niveau B · Ta copie complète sur ton portable, sans Telegram

Tu obtiens **exactement** le même assistant que Fedi :
- même graphe de 42 nœuds, mêmes données et mêmes outils ;
- tu l'interroges par la **porte de test** (`http://127.0.0.1:5678/webhook/wf3-test`), avec `smoke_wf3.py` ou ton banc d'essai ;
- tu vois tout dans **ton** n8n.

### Ce qu'il faut
- **Windows 10/11 avec Docker Desktop** (WSL2), ou Linux avec Docker ; **Git** ; **Python 3.11+**.
- **16 Go de RAM minimum**, et environ 15 Go de disque libre (images + modèles).
- Une **clé API Gemini gratuite** à toi : Google AI Studio → *Get API key*. Elle sert au mode hybride, celui par défaut.
  - Sans clé, tu peux passer en mode `local`. C'est très lent : environ 170 s par question réglementaire.

### Étapes

1. **Mémoire Docker (Windows).**
   - Crée `%UserProfile%\.wslconfig` avec ce contenu :
     ```ini
     [wsl2]
     memory=12GB
     swap=8GB
     ```
   - Puis lance `wsl --shutdown` et redémarre Docker Desktop.
2. **Le dépôt et Python :**
   ```powershell
   git pull
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
3. **Le fichier `.env`** (il reste sur ta machine, jamais dans Git) :
   ```powershell
   Copy-Item .env.example .env
   # génère TA clé de chiffrement n8n (une fois ; garde-la : si tu la perds, tes credentials sont illisibles)
   $b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b)
   ```
   Ouvre `.env` et remplis-le :
   ```
   N8N_ENCRYPTION_KEY=<la valeur générée>
   WEBHOOK_URL=http://localhost:5678/
   NGROK_AUTHTOKEN=unused
   NGROK_DOMAIN=unused.example
   ```
   Les deux lignes `NGROK_*` sont des valeurs bidon : sans Telegram, ngrok ne démarre pas, mais Docker veut que les variables existent.
4. **Démarre n8n une première fois et crée ton compte propriétaire :**
   ```powershell
   docker compose up -d n8n qdrant ollama
   ```
   - Ouvre http://localhost:5678 et crée **ton** compte : ton e-mail et un mot de passe solide.
   - Ignore l'assistant IA de n8n.
5. **Lance l'installation** (elle demande ta clé Gemini en saisie cachée) :
   ```powershell
   .venv\Scripts\python -X utf8 scripts\setup\bootstrap.py --gemini
   ```
   Le script fait tout le reste et affiche ✓ à chaque étape :
   - les modèles (environ 3,7 Go la première fois) ;
   - les credentials, avec les identifiants attendus par les workflows ;
   - l'import et la publication des workflows ;
   - l'indexation des règlements dans Qdrant (5–6 min, 168 + 77 points).

   Tu peux le relancer sans risque : chaque étape vérifie d'abord ce qui existe déjà.
6. **Vérifie que tout marche :**
   ```powershell
   .venv\Scripts\python -X utf8 scripts\workflows\smoke_wf3.py
   ```
   - **Attendu :** `9/9 valid`, et le détail des réponses dans `eval/agents/wf3_smoke.md`.
   - Ouvre ensuite n8n → **Executions** pour voir chaque exécution, nœud par nœud.

### Travailler avec ta copie

- **Tester un nouveau prompt (Ines) :**
  - écris la version (par exemple `<!-- template:v3 -->`) dans `prompts/P-REGULATIONS-001.md` ;
  - pointe `config/agents.json` dessus (`"P-REGULATIONS-001@v3"`) ;
  - régénère avec `.venv\Scripts\python -X utf8 scripts\workflows\build_wf3.py` ;
  - relance `smoke_wf3.py`, qui réimporte les workflows.
- **Banc d'essai (Doua) :**
  - vise `http://127.0.0.1:5678/webhook/wf3-test` ;
  - la porte n'est ouverte que pendant un test : `smoke_wf3.py` l'ouvre et la ferme. Pour ton banc d'essai, ouvre-la et ferme-la avec les deux commandes de `eval/e2e/CONTRACT.md`.
- **Mode local, sans clé Gemini :** mets `"mode": "local"` dans `config/agents.json`, relance `build_wf3.py`, puis `smoke_wf3.py`.
- **Ne commite jamais ces changements de test sur `main`.** Seules les versions validées sont fusionnées, par Fedi.
- **Ne publie aucune URL :** sans ngrok, ta copie n'est joignable que depuis ton portable (ports liés à `127.0.0.1`).

---

## Niveau C · Ta copie avec TON propre bot Telegram

C'est le niveau B, plus 3 choses :

1. **Ton bot :**
   - dans Telegram, écris à **@BotFather** → `/newbot` → choisis un nom et un identifiant qui finit par `bot` (par exemple `DouaCampusTestBot`) ;
   - copie le **token**. C'est un secret : ne le colle nulle part ailleurs que dans le script.
2. **Ton tunnel ngrok gratuit :**
   - crée un compte sur ngrok.com ;
   - *Your Authtoken* → copie-le ;
   - *Domains* → ton domaine gratuit.

   Dans `.env` :
   ```
   NGROK_AUTHTOKEN=<ton authtoken>
   NGROK_DOMAIN=<ton-domaine>.ngrok-free.dev
   WEBHOOK_URL=https://<ton-domaine>.ngrok-free.dev/
   ```
3. **Relance l'installation avec Telegram :**
   ```powershell
   .venv\Scripts\python -X utf8 scripts\setup\bootstrap.py --gemini --telegram
   ```
   - Le script vérifie auprès de Telegram que le token est valide et que ce n'est **pas** celui de @CampusFlowAI_bot.
   - Il démarre ensuite ngrok et publie l'entrée Telegram.
   - Ouvre **ton** bot, appuie sur Démarrer et pose la question du calendrier.

**Attention :** ton n8n est alors joignable depuis Internet par ton domaine ngrok. Garde un mot de passe n8n solide, et arrête ngrok quand tu ne testes pas : `docker compose stop ngrok`.

---

## Ce qu'il ne faut jamais faire

- Utiliser le token de @CampusFlowAI_bot ailleurs que sur le portable de démo : ça vole le bot.
- Mettre une clé, un token ou un mot de passe dans un fichier du dépôt, un commit, un message Jira ou WhatsApp. `.env` reste local.
- Laisser `03b_wf3_test`, la porte de test, publiée avec ngrok actif : elle serait publique.
- Changer `N8N_ENCRYPTION_KEY` après l'installation : toutes tes credentials deviendraient illisibles.

## Problèmes fréquents

| Symptôme | Cause | Solution |
|---|---|---|
| `Set N8N_ENCRYPTION_KEY / NGROK_* in .env` | `.env` incomplet | Étape 3 (valeurs bidon pour `NGROK_*` au niveau B) |
| Le script dit « n8n has no owner account yet » | Compte propriétaire pas encore créé | http://localhost:5678 → crée-le → relance |
| Les réponses réglementaires échouent, alors que le calendrier marche | Mode hybride sans clé Gemini | Relance avec `--gemini`, ou passe en mode `local` |
| Une requête Ollama prend des minutes | Pas assez de RAM pour Docker | `.wslconfig` (étape 1) ; ferme Chrome et les autres applications |
| Mon bot ne répond pas | ngrok arrêté, mauvais `WEBHOOK_URL`, ou message envoyé à @BotFather | `docker compose logs ngrok` ; `WEBHOOK_URL` = ton domaine avec `/` à la fin |
| « could not decrypt » dans n8n | `N8N_ENCRYPTION_KEY` modifiée | Remets l'ancienne clé dans `.env`, puis `docker compose up -d n8n` |
