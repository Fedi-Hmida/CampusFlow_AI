"""CF-008c — agent tool-calling test.

Sends 10 French questions to the n8n workflow 00b_agent_tool_test (AI Agent + Ollama + calculator + lookup_exam +
Structured Output Parser) and checks, per run, which tool the agent called, whether the final output matches the
JSON schema, and how long it took.

Usage:  python eval/agents/agent_tool_test.py <model> <zero|fewshot> [--url http://127.0.0.1:5678/webhook/agent-tool-test]
Prints one JSON line per run, then a summary line.
"""
import argparse
import json
import time
import urllib.request

ZERO_SHOT = (
    "Tu es un assistant de test pour des étudiants d'ESPRIT. Tu as deux outils : "
    "lookup_exam (date, heure, salle d'un examen) et calculator (tout calcul numérique). "
    "Utilise lookup_exam pour toute question sur la date, le jour, l'heure ou la salle d'un examen. "
    "Utilise calculator pour tout calcul. Sinon, réponds directement sans outil. "
    "Ne devine jamais une date ou une salle : elles viennent uniquement de lookup_exam. Réponds en français."
)

FEW_SHOT = ZERO_SHOT + (
    "\n\nExemples :\n"
    "- « C'est quand l'examen de MA21 pour 3A2 ? » → appelle lookup_exam avec « MA21 3A2 », puis réponds avec la date, "
    "l'heure et la salle ; tool_used = lookup_exam ; sources = [\"exam_calendar\"].\n"
    "- « Combien font 18 fois 4 ? » → appelle calculator avec « 18*4 » ; tool_used = calculator ; sources = [].\n"
    "- « Ma moyenne avec 10 (coef 0.3) et 16 (coef 0.7) ? » → appelle calculator avec « 10*0.3+16*0.7 » ; "
    "tool_used = calculator.\n"
    "- « Salut, tu fais quoi ? » → aucun outil ; tool_used = none ; sources = [].\n"
    "- « Traduis 'examen' en anglais. » → aucun outil ; tool_used = none."
)

CASES = [
    ("lookup_exam", "Quand est mon examen de DS14 ? Je suis en 5DS6."),
    ("lookup_exam", "Dans quelle salle se passe l'examen DS14 pour la classe 5DS6 ?"),
    ("lookup_exam", "À quelle heure commence l'épreuve de DS14 ?"),
    ("lookup_exam", "Donne-moi la date de l'examen du module DS14."),
    ("lookup_exam", "J'ai DS14 en 5DS6, c'est quel jour et où ?"),
    ("calculator", "Combien font 245 divisé par 7 ?"),
    ("calculator", "Calcule la moyenne de 12, 15 et 9."),
    ("calculator", "J'ai 14/20 au DS (coef 0.4) et 11/20 à l'examen (coef 0.6). Quelle est ma note finale ?"),
    ("none", "Bonjour, qui es-tu ?"),
    ("none", "Traduis « session de rattrapage » en anglais."),
]

# Internal tools n8n may add around the output parser; they do not count as a business tool call.
INTERNAL_TOOLS = {"format_final_json_response", "format_final_response"}


def call(url: str, body: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def tools_called(resp: dict) -> list[str]:
    steps = resp.get("intermediateSteps") or []
    names = [(s.get("action") or {}).get("tool") for s in steps]
    return [n for n in names if n and n not in INTERNAL_TOOLS]


def valid_output(resp: dict) -> bool:
    out = resp.get("output")
    if isinstance(out, str):
        try:
            out = json.loads(out)
        except ValueError:
            return False
    return (
        isinstance(out, dict)
        and isinstance(out.get("answer"), str)
        and isinstance(out.get("tool_used"), str)
        and isinstance(out.get("sources"), list)
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("prompt", choices=["zero", "fewshot"])
    ap.add_argument("--url", default="http://127.0.0.1:5678/webhook/agent-tool-test")
    a = ap.parse_args()
    system = ZERO_SHOT if a.prompt == "zero" else FEW_SHOT
    ok_tool = ok_json = 0
    total = 0.0
    for i, (expected, question) in enumerate(CASES, 1):
        t = time.time()
        try:
            resp = call(a.url, {"question": question, "model": a.model, "system": system})
            if isinstance(resp, list):
                resp = resp[0] if resp else {}
        except Exception as e:  # network error or n8n 500
            resp = {"error": str(e)}
        dt = time.time() - t
        total += dt
        called = tools_called(resp)
        correct = (expected in called) if expected != "none" else (called == [])
        valid = valid_output(resp)
        ok_tool += correct
        ok_json += valid
        out = resp.get("output")
        print(json.dumps({
            "run": i, "expected": expected, "called": called, "correct_tool": correct, "valid_json": valid,
            "seconds": round(dt, 1), "output": out if out is not None else str(resp)[:400],
        }, ensure_ascii=False), flush=True)
    print(json.dumps({
        "summary": True, "model": a.model, "prompt": a.prompt, "correct_tool": f"{ok_tool}/10",
        "valid_json": f"{ok_json}/10", "avg_seconds": round(total / len(CASES), 1),
        "pass": ok_tool >= 9 and ok_json >= 9,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
