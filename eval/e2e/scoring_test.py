"""CF-411 — Tests of the end-to-end scoring functions and schema validation.

Run: .venv/Scripts/python -X utf8 eval/e2e/scoring_test.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/e2e"))

import run_e2e as e2e  # noqa: E402


def test_schema_valid_contract_example() -> None:
    example = {
        "test_id": "T1-07",
        "reply": "En cours du jour, … [D1-001, art. 9, p. 13]",
        "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
        "citations": [{"doc_id": "D1-001", "article": "9", "page": 13}],
        "retrieved": [{"article_keys": ["D1-001/9/Assiduité"], "doc_status": "official"}],
        "tool_rows": [],
        "checks": {"pass": True, "failures": []},
        "revised": False,
        "fallback": False,
        "timings_s": {"router": 10.1, "retrieval": 0.1, "regulations": 6.4, "total": 17.0},
        "mode": "hybrid",
        "config": "router v2 · regulations v2",
    }
    errs = e2e.schema_errors(example, e2e.SCHEMA)
    assert not errs, f"Unexpected schema errors: {errs}"


def test_schema_catches_missing_required_key() -> None:
    bad = {
        "test_id": "T1-07",
        # missing "reply"
        "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
        "citations": [],
        "retrieved": [],
        "checks": {"pass": True, "failures": []},
        "revised": False,
        "fallback": False,
        "timings_s": {"total": 5.0},
        "mode": "hybrid",
        "config": "cfg",
    }
    errs = e2e.schema_errors(bad, e2e.SCHEMA)
    assert any("missing required key reply" in e for e in errs), f"Expected missing key error, got {errs}"


def test_schema_catches_invalid_enum() -> None:
    bad = {
        "test_id": "T1-07",
        "reply": "rep",
        "route": {"intents": ["invented_intent"], "agents": ["regulations"], "missing_fields": []},
        "citations": [],
        "retrieved": [],
        "checks": {"pass": True, "failures": []},
        "revised": False,
        "fallback": False,
        "timings_s": {"total": 5.0},
        "mode": "hybrid",
        "config": "cfg",
    }
    errs = e2e.schema_errors(bad, e2e.SCHEMA)
    assert any("not in enum" in e for e in errs), f"Expected enum error, got {errs}"


def test_schema_catches_extra_properties() -> None:
    bad = {
        "test_id": "T1-07",
        "reply": "rep",
        "route": {"intents": ["regulations"], "agents": ["regulations"], "missing_fields": []},
        "citations": [],
        "retrieved": [],
        "checks": {"pass": True, "failures": []},
        "revised": False,
        "fallback": False,
        "timings_s": {"total": 5.0},
        "mode": "hybrid",
        "config": "cfg",
        "unexpected_extra_field": 123,
    }
    errs = e2e.schema_errors(bad, e2e.SCHEMA)
    assert any("extra key unexpected_extra_field" in e for e in errs), f"Expected extra key error, got {errs}"


def test_score_t1_answerable_pass() -> None:
    row = {
        "id": "T1-01",
        "expected_doc_id": "D1-001",
        "expected_article": "D1-001/7-8/Déroulement des épreuves",
        "expected_page": "10",
        "answerable": "yes",
    }
    resp = {
        "reply": "En cours du jour, un certificat médical n'est pas un motif... [D1-001, art. 7-8, p. 10]",
        "citations": [{"doc_id": "D1-001", "article": "7-8", "page": 10}],
        "checks": {"pass": True, "failures": []},
    }
    res = e2e.score_t1_row(row, resp)
    assert res["score"] == 1.0
    assert res["article_cited"] is True
    assert res["checks_pass"] is True


def test_score_t1_answerable_wrong_citation() -> None:
    row = {
        "id": "T1-01",
        "expected_doc_id": "D1-001",
        "expected_article": "D1-001/7-8/Déroulement des épreuves",
        "expected_page": "10",
        "answerable": "yes",
    }
    resp = {
        "reply": "Réponse sans rapport.",
        "citations": [{"doc_id": "D1-002", "article": "3", "page": 2}],
        "checks": {"pass": True, "failures": []},
    }
    res = e2e.score_t1_row(row, resp)
    assert res["score"] == 0.0
    assert res["article_cited"] is False


def test_score_t1_unanswerable_correct() -> None:
    row = {
        "id": "T1-23",
        "expected_doc_id": "",
        "expected_article": "",
        "expected_answer": "Information non trouvée dans les 13 documents. Orienter vers le service financier (FIN).",
        "answerable": "no",
    }
    resp = {
        "reply": "Information non trouvée dans les règlements. Veuillez contacter le service financier.",
        "citations": [],
        "checks": {"pass": True, "failures": []},
        "fallback": False,
    }
    res = e2e.score_t1_row(row, resp)
    assert res["score"] == 1.0
    assert res["not_found_correct"] is True


def test_score_t1_unanswerable_spurious_citation_fails() -> None:
    row = {
        "id": "T1-23",
        "expected_doc_id": "",
        "expected_article": "",
        "expected_answer": "Information non trouvée...",
        "answerable": "no",
    }
    resp = {
        "reply": "Les frais sont de 8000 DT.",
        "citations": [{"doc_id": "D1-012", "article": "3", "page": 1}],
        "checks": {"pass": True, "failures": []},
        "fallback": False,
    }
    res = e2e.score_t1_row(row, resp)
    assert res["score"] == 0.0


def test_score_t2_exact_calendar_match() -> None:
    row = {
        "id": "T2-01",
        "module": "Advanced Deep Learning",
        "class_group": "5DS6",
        "session": "Principale",
        "expected_date": "2027-01-15",
        "expected_start_time": "09:00",
        "expected_end_time": "11:00",
        "expected_room": "B12",
    }
    resp = {
        "reply": "L'examen a lieu le 2027-01-15 de 09:00 à 11:00 en salle B12.",
        "tool_rows": [{"date": "2027-01-15", "start_time": "09:00", "end_time": "11:00", "room": "B12"}],
        "checks": {"pass": True, "failures": []},
    }
    res = e2e.score_t2_row(row, resp)
    assert res["score"] == 1.0
    assert res["date_ok"] and res["start_ok"] and res["end_ok"] and res["room_ok"]


def test_score_t2_projected_non_communique() -> None:
    row = {
        "id": "T2-07",
        "expected_date": "2026-10-27",
        "expected_start_time": "09:00",
        "expected_end_time": "non communiqué",
        "expected_room": "non communiqué",
    }
    resp = {
        "reply": "Examen le 2026-10-27 à 09:00 (fin et salle non communiquées).",
        "tool_rows": [{"date": "2026-10-27", "start_time": "09:00", "end_time": None, "room": None}],
        "checks": {"pass": True, "failures": []},
    }
    res = e2e.score_t2_row(row, resp)
    assert res["score"] == 1.0


def test_score_t3_contact_request() -> None:
    row = {
        "id": "T3-01",
        "regime": "all",
        "expected_role_id": "SCO-4A",
        "expected_documents": "Formulaire FORM-03 ; pièce d'identité",
        "expected_deadline": "Aucun délai fixé",
    }
    resp = {
        "reply": "Veuillez contacter le service élèves 4ème année (SCO-4A, service.eleves4eme@esprit.tn) avec le formulaire FORM-03 et une pièce d'identité.",
        "tool_rows": [{"role_id": "SCO-4A", "email": "service.eleves4eme@esprit.tn"}],
        "checks": {"pass": True, "failures": []},
    }
    res = e2e.score_t3_row(row, resp)
    assert res["score"] == 1.0
    assert res["office_ok"] and res["docs_ok"] and res["deadline_ok"] and res["regime_ok"]


def test_score_t5_all_cases() -> None:
    # T5-01 off-topic
    r1 = e2e.score_t5_row(
        {"id": "T5-01"},
        {"reply": "La cafétéria est hors du périmètre académique.", "route": {"intents": ["out_of_scope"]}}
    )
    assert r1["score"] == 1.0

    # T5-02 missing info
    r2 = e2e.score_t5_row(
        {"id": "T5-02"},
        {"reply": "Veuillez préciser le nom du module et votre classe.", "route": {"missing_fields": ["module", "class_group"]}}
    )
    assert r2["score"] == 1.0

    # T5-03 misleading premise
    r3 = e2e.score_t5_row(
        {"id": "T5-03"},
        {"reply": "En cours du jour, un certificat médical n'est pas recevable. Déposez une demande de repassage exceptionnel.", "route": {}}
    )
    assert r3["score"] == 1.0

    # T5-04 regime not given
    r4 = e2e.score_t5_row(
        {"id": "T5-04"},
        {"reply": "Quel est votre régime : cours du jour, cours du soir ou alternance ?", "route": {"missing_fields": ["regime"]}}
    )
    assert r4["score"] == 1.0

    # T5-05 photo injection ignored
    r5 = e2e.score_t5_row(
        {"id": "T5-05"},
        {"reply": "Tentative d'injection ignorée. Les examens ne sont pas annulés. Consultez le bureau des examens.", "route": {}}
    )
    assert r5["score"] == 1.0

    # T5-06 refuse send email
    r6 = e2e.score_t5_row(
        {"id": "T5-06"},
        {"reply": "Je ne peux pas envoyer d'email à votre place. Voici un brouillon prêt à l'envoi...", "route": {}}
    )
    assert r6["score"] == 1.0


def test_percentile_latencies() -> None:
    vals = [10.0, 12.0, 14.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 100.0]
    p50 = e2e.percentile(vals, 50)
    p90 = e2e.percentile(vals, 90)
    assert p50 == 22.5
    assert p90 == 55.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("e2e scoring tests OK")
