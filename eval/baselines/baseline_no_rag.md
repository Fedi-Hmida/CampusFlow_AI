# Baseline without RAG

What the bare agent model answers **without any retrieved regulation text**. The RAG pipeline (Phases 2–4) must fix
these answers; they are the "before" in the report's before/after comparison.

| # | Date | Question (as sent on Telegram) | Model | Answer | Verdict |
|---|---|---|---|---|---|
| B1 | 24 Oct 2026, 21:39 (Europe/Paris) | Quest ce qu’une session de rattrapage | `qwen3:4b-instruct-2507-q4_K_M` (Ollama, CPU, prompt: "Réponds en une seule phrase en français : …") | « Une session de rattrapage est une séance organisée pour permettre aux élèves de corriger ou de réviser des connaissances ou des devoirs non suivis ou mal compris. » | ❌ Wrong: describes a revision/catch-up class. A *session de rattrapage* is the **retake exam session** for students who failed (or missed) the main session (*session principale*). No source, no article cited. |
| B2 | 24 Oct 2026 (Europe/Paris) | Photo of a FICTITIOUS ESPRIT convocation (DS14, 15/01/2027) + caption « J’étais malade, je peux le rattraper ? » | `qwen3:4b-instruct-2507-q4_K_M` (text only; in the smoke test the photo goes to Gemini but its facts are **not** passed to the chat model) | « Oui, tu peux le rattraper, même si tu étais malade. » | ❌ Wrong: unconditional "yes", no source, ignores the 48-hour justification rule printed on the document; no office, no required document (medical certificate), no deadline. Gemini read the photo correctly (« convocation … 15/01/2027 ») but nothing used it. |

Sources: n8n workflow `00_smoke_test`, execution #2 (B1, 5.5 s) and #3 (B2, 5.7 s, photo path through Gemini).

## Expected after RAG
A grounded answer citing the regulation (document, article, page), e.g. the rule defining who may sit the
*session de rattrapage*, and "not found" + the right office if the corpus has no such rule (FR-01, FR-09, NFR-05).
- **B2:** example flow 2 of the spec (§8): Vision (DS14, session, 15/01) + Regulations (absence/retake article) + Admin
  (registrar, medical certificate, 48 h deadline, draft message) → Composer → Critic (FR-05, FR-06).
