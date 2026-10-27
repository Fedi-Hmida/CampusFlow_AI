"""CF-411 — Stub WF-3 webhook server for end-to-end evaluation.

Simulates the assistant test endpoint (POST http://127.0.0.1:5699/webhook/wf3-test; 5699, never n8n's 5678)
as specified in eval/e2e/CONTRACT.md and eval/e2e/wf3_response.schema.json.

Can return:
- 'correct': accurate answers matching ground truth test sets T1, T2, T3, T5
- 'wrong': incorrect citations / mismatched answers
- 'not_found': 'information non trouvée' fallback answers
- 'invalid_json': malformed JSON or schema-invalid response

Run:
  .venv/Scripts/python eval/e2e/stub_wf3.py [--port 5699] [--behavior correct|wrong|not_found|invalid_json]
"""
import argparse
import csv
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load_testsets() -> dict[str, dict[str, dict[str, str]]]:
    """Load T1, T2, T3, T5 data keyed by question ID."""
    sets: dict[str, dict[str, dict[str, str]]] = {"T1": {}, "T2": {}, "T3": {}, "T5": {}}
    t1_p = ROOT / "eval/testsets/T1_regulations.csv"
    if t1_p.exists():
        with open(t1_p, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                sets["T1"][row["id"]] = row
    t2_p = ROOT / "eval/testsets/T2_calendar.csv"
    if t2_p.exists():
        with open(t2_p, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                sets["T2"][row["id"]] = row
    t3_p = ROOT / "eval/testsets/T3_contacts_requests.csv"
    if t3_p.exists():
        with open(t3_p, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                sets["T3"][row["id"]] = row
    t5_p = ROOT / "eval/testsets/T5_adversarial.csv"
    if t5_p.exists():
        with open(t5_p, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                sets["T5"][row["id"]] = row
    return sets


DATASETS = load_testsets()


def make_stub_response(req: dict[str, Any], default_behavior: str = "correct") -> tuple[int, str]:
    """Generate HTTP status code and body string for a given request."""
    behavior = req.get("stub_behavior", default_behavior)
    test_id = req.get("test_id", "T1-01")
    mode = req.get("mode", "hybrid")
    if mode not in ("hybrid", "local"):
        mode = "hybrid"

    if behavior == "invalid_json":
        # Return malformed JSON string
        return 200, '{"test_id": "' + test_id + '", "reply": "incomplete JSON...'

    if behavior == "not_found":
        body = {
            "test_id": test_id,
            "reply": "Information non trouvée dans les documents du corpus. Veuillez vous adresser au service de la scolarité générale (service.scolarite@esprit.tn).",
            "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
            "citations": [],
            "retrieved": [],
            "tool_rows": [],
            "checks": {"pass": True, "failures": []},
            "revised": False,
            "fallback": True,
            "timings_s": {"total": 12.0 if mode == "hybrid" else 105.0, "router": 1.2, "retrieval": 0.1, "regulations": 10.7},
            "mode": mode,
            "config": "router v2 · regulations v2",
        }
        return 200, json.dumps(body, ensure_ascii=False)

    if behavior == "wrong":
        body = {
            "test_id": test_id,
            "reply": "Ceci est une réponse erronée ne citant pas le bon document ni les bonnes dates.",
            "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
            "citations": [{"doc_id": "D1-999", "article": "99", "page": 99}],
            "retrieved": [{"article_keys": ["D1-999/99/Inconnu"], "doc_status": "official"}],
            "tool_rows": [],
            "checks": {"pass": False, "failures": ["unknown doc_id D1-999"]},
            "revised": True,
            "fallback": False,
            "timings_s": {"total": 15.0 if mode == "hybrid" else 110.0, "router": 1.5, "retrieval": 0.1, "regulations": 13.4},
            "mode": mode,
            "config": "router v2 · regulations v2",
        }
        return 200, json.dumps(body, ensure_ascii=False)

    # Behavior == "correct": generate realistic correct response per set
    prefix = test_id.split("-")[0] if "-" in test_id else "T1"

    if prefix == "T1":
        row = DATASETS["T1"].get(test_id, {})
        answerable = row.get("answerable", "yes") == "yes"
        if not answerable:
            reply = "Information non trouvée dans les 13 documents du corpus réglementaire. "
            if "FIN" in row.get("expected_answer", ""):
                reply += "Veuillez vous adresser au service financier (finance@esprit.tn)."
            elif "STAGE" in row.get("expected_answer", ""):
                reply += "Veuillez contacter le département des stages (stages@esprit.tn) et la mobilité internationale (mobilite-internationale@esprit.tn)."
            else:
                reply += "Veuillez contacter la scolarité générale (service.scolarite@esprit.tn)."
            body = {
                "test_id": test_id,
                "reply": reply,
                "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
                "citations": [],
                "retrieved": [],
                "tool_rows": [],
                "checks": {"pass": True, "failures": []},
                "revised": False,
                "fallback": False,
                "timings_s": {"total": 14.1 if mode == "hybrid" else 112.5, "router": 1.2, "retrieval": 0.1, "regulations": 12.8},
                "mode": mode,
                "config": "router v2 · regulations v2",
            }
        else:
            doc_id_raw = row.get("expected_doc_id", "D1-001")
            art_raw = row.get("expected_article", "")
            page_raw = row.get("expected_page", "1")
            first_doc = doc_id_raw.split("|")[0].strip()
            first_art = art_raw.split("|")[0].strip()
            art_num = first_art.split("/")[1] if "/" in first_art else first_art
            try:
                page_num = int(page_raw.split("|")[0].strip())
            except ValueError:
                page_num = 1

            doc_num = int(first_doc.split("-")[1]) if "-" in first_doc else 1
            doc_status = "official" if doc_num <= 3 else "FICTITIOUS"

            exp_ans = row.get("expected_answer", "")
            reply = f"{exp_ans} [{first_doc}, art. {art_num}, p. {page_num}]"

            body = {
                "test_id": test_id,
                "reply": reply,
                "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
                "citations": [{"doc_id": first_doc, "article": art_num, "page": page_num}],
                "retrieved": [{"article_keys": [first_art], "doc_status": doc_status}],
                "tool_rows": [],
                "checks": {"pass": True, "failures": []},
                "revised": False,
                "fallback": False,
                "timings_s": {"total": 13.8 if mode == "hybrid" else 114.0, "router": 1.1, "retrieval": 0.1, "regulations": 12.6},
                "mode": mode,
                "config": "router v2 · regulations v2",
            }

    elif prefix == "T2":
        row = DATASETS["T2"].get(test_id, {})
        d = row.get("expected_date", "")
        st = row.get("expected_start_time", "")
        et = row.get("expected_end_time", "")
        rm = row.get("expected_room", "")
        mod = row.get("module", "")
        cls_grp = row.get("class_group", "")
        sess = row.get("session", "")

        if d == "not found":
            reply = f"Aucun examen trouvé dans le calendrier pour le module {mod} en classe {cls_grp} ({sess})."
            tool_rows = []
        elif "pas encore publié" in d:
            reply = f"L'épreuve de rattrapage pour {mod} en {cls_grp} n'est pas encore publiée (date et salle non communiquées)."
            tool_rows = [{"module": mod, "class_group": cls_grp, "session": sess, "status": "not_published"}]
        else:
            parts = [f"L'examen de {mod} pour la classe {cls_grp} ({sess}) aura lieu le {d}"]
            if st and st != "non communiqué":
                parts.append(f"à partir de {st}")
            if et and et != "non communiqué":
                parts.append(f"jusqu'à {et}")
            if rm and rm != "non communiqué":
                parts.append(f"en salle {rm}")
            else:
                parts.append("(salle non communiquée)")
            reply = " ".join(parts) + "."
            tool_rows = [{"module": mod, "class_group": cls_grp, "session": sess, "date": d,
                          "start_time": st if st != "non communiqué" else None,
                          "end_time": et if et != "non communiqué" else None,
                          "room": rm if rm != "non communiqué" else None}]

        body = {
            "test_id": test_id,
            "reply": reply,
            "route": {"intents": ["calendar"], "agents": ["calendar"], "missing_fields": []},
            "citations": [],
            "retrieved": [],
            "tool_rows": tool_rows,
            "checks": {"pass": True, "failures": []},
            "revised": False,
            "fallback": False,
            "timings_s": {"total": 8.5 if mode == "hybrid" else 11.2, "router": 1.0, "tools": 0.5},
            "mode": mode,
            "config": "router v2 · tools",
        }

    elif prefix == "T3":
        row = DATASETS["T3"].get(test_id, {})
        role_id = row.get("expected_role_id", "SCO-GEN")
        docs = row.get("expected_documents", "")
        deadline = row.get("expected_deadline", "")

        # Map role_id to email
        role_emails = {
            "SCO-GEN": "service.scolarite@esprit.tn",
            "SCO-3A": "service.eleves3eme@esprit.tn",
            "SCO-4A": "service.eleves4eme@esprit.tn",
            "STAGE": "stages@esprit.tn",
            "MOB": "mobilite-internationale@esprit.tn",
            "FIN": "finance@esprit.tn",
            "EXA": "examen@esprit.tn",
            "DEP-HEAD": "chef.departement@esprit.tn",
        }
        email = role_emails.get(role_id, "service.scolarite@esprit.tn")

        parts = [f"Vous devez contacter le service correspondant ({role_id}, e-mail: {email})."]
        if docs and docs != "—":
            parts.append(f"Pièces requises : {docs}.")
        if deadline and deadline != "—":
            parts.append(f"Délai : {deadline}.")
        reply = " ".join(parts)

        tool_rows = [{"role_id": role_id, "email": email, "documents": docs, "deadline": deadline}]
        body = {
            "test_id": test_id,
            "reply": reply,
            "route": {"intents": ["admin"], "agents": ["admin"], "missing_fields": []},
            "citations": [],
            "retrieved": [],
            "tool_rows": tool_rows,
            "checks": {"pass": True, "failures": []},
            "revised": False,
            "fallback": False,
            "timings_s": {"total": 9.2 if mode == "hybrid" else 12.4, "router": 1.1, "tools": 0.6},
            "mode": mode,
            "config": "router v2 · admin v2",
        }

    elif prefix == "T5":
        row = DATASETS["T5"].get(test_id, {})
        case_type = row.get("case_type", "")
        if test_id == "T5-01" or case_type == "off-topic":
            reply = "Je suis l'assistant étudiant d'ESPRIT, dédié aux règlements, examens et démarches administratives. La cafétéria ne relève pas de mes services."
            route = {"intents": ["out_of_scope"], "agents": [], "missing_fields": []}
            citations = []
        elif test_id == "T5-02" or case_type == "missing info":
            reply = "Pour trouver la date et la salle de votre examen, veuillez préciser le nom du module et votre classe."
            route = {"intents": ["calendar"], "agents": ["calendar"], "missing_fields": ["module", "class_group"]}
            citations = []
        elif test_id == "T5-03" or case_type == "misleading premise":
            reply = "Attention : en cours du jour, un certificat médical n'est pas un motif valable pour justifier une absence d'examen [D1-001, art. 7-8, p. 10]. Vous devez déposer un dossier de repassage exceptionnel (REQ-08-J)."
            route = {"intents": ["regulations", "admin"], "agents": ["regulations", "admin"], "missing_fields": []}
            citations = [{"doc_id": "D1-001", "article": "7-8", "page": 10}]
        elif test_id == "T5-04" or case_type == "regime not given":
            reply = "Les règles d'absence diffèrent selon votre régime d'études. Êtes-vous en cours du jour, cours du soir ou alternance ?"
            route = {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": ["regime"]}
            citations = []
        elif test_id == "T5-05" or case_type == "instruction inside a photo":
            reply = "Le texte mentionné sur le post-it est une tentative d'injection. Aucun examen n'est annulé. En cas de doute, consultez le bureau des examens (examen@esprit.tn)."
            route = {"intents": ["calendar"], "agents": ["calendar"], "missing_fields": []}
            citations = []
        elif test_id == "T5-06" or case_type == "send email for the student":
            reply = "Je ne peux pas envoyer d'e-mail à votre place. Voici un modèle prêt à l'envoi pour le service élèves 4ème année (service.eleves4eme@esprit.tn) :\nObjet: Demande de relevé de notes\nMadame, Monsieur..."
            route = {"intents": ["admin"], "agents": ["admin"], "missing_fields": []}
            citations = []
        else:
            reply = "Traitement adversarial standard."
            route = {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []}
            citations = []

        body = {
            "test_id": test_id,
            "reply": reply,
            "route": route,
            "citations": citations,
            "retrieved": [],
            "tool_rows": [],
            "checks": {"pass": True, "failures": []},
            "revised": False,
            "fallback": False,
            "timings_s": {"total": 8.0 if mode == "hybrid" else 15.0, "router": 1.0},
            "mode": mode,
            "config": "router v2 · regulations v2",
        }

    else:
        body = {
            "test_id": test_id,
            "reply": "Réponse générique du stub.",
            "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
            "citations": [],
            "retrieved": [],
            "tool_rows": [],
            "checks": {"pass": True, "failures": []},
            "revised": False,
            "fallback": False,
            "timings_s": {"total": 5.0, "router": 1.0},
            "mode": mode,
            "config": "router v2",
        }

    return 200, json.dumps(body, ensure_ascii=False)


class StubRequestHandler(BaseHTTPRequestHandler):
    behavior: str = "correct"

    def do_POST(self) -> None:
        if not (self.path == "/webhook/wf3-test" or self.path.startswith("/webhook/wf3-test?")):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        try:
            req_data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON in request")
            return

        status, resp_body = make_stub_response(req_data, default_behavior=self.behavior)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(resp_body.encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy HTTP server logs unless debugging
        pass


def run_server(port: int = 5699, behavior: str = "correct") -> None:
    server_address = ("127.0.0.1", port)
    handler = StubRequestHandler
    handler.behavior = behavior
    httpd = HTTPServer(server_address, handler)
    print(f"Stub WF-3 listening on http://127.0.0.1:{port}/webhook/wf3-test (behavior: {behavior})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping stub server.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WF-3 test webhook stub server")
    parser.add_argument("--port", type=int, default=5699, help="Port to listen on (default: 5699, never n8n's 5678)")
    parser.add_argument("--behavior", choices=["correct", "wrong", "not_found", "invalid_json"],
                        default="correct", help="Stub behavior mode (default: correct)")
    args = parser.parse_args()
    run_server(port=args.port, behavior=args.behavior)
