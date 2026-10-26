"""CF-400 — tests of eval/agents/gemini_client.py (no network: urlopen is replaced). Run: python -X utf8 eval/agents/gemini_client_test.py"""
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gemini_client as gc  # noqa: E402

FAKE_KEY = "test-key-not-a-secret-123"
SENT = {}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(req, timeout=0):
    SENT["url"], SENT["headers"], SENT["body"] = req.full_url, dict(req.header_items()), json.loads(req.data.decode())
    body = {"candidates": [{"content": {"parts": [{"text": "réponse"}]}}], "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 3}}
    return FakeResponse(json.dumps(body).encode())


def test_direct_puts_the_key_in_a_header_not_the_url() -> None:
    os.environ["GEMINI_API_KEY"] = FAKE_KEY
    gc.urllib.request.urlopen = fake_urlopen
    out = gc.generate("système", "question", via="direct")
    assert out["text"] == "réponse" and out["prompt_tokens"] == 10 and out["output_tokens"] == 3
    assert FAKE_KEY not in SENT["url"]
    assert {k.lower(): v for k, v in SENT["headers"].items()}["x-goog-api-key"] == FAKE_KEY
    assert SENT["body"]["systemInstruction"]["parts"][0]["text"] == "système"
    assert SENT["body"]["generationConfig"]["temperature"] == 0.1


def test_direct_with_an_image_sends_inline_data(tmp=Path(__file__).resolve().parents[2] / "eval/testsets/T4_photos/T4-11_unrelated_menu.png") -> None:
    os.environ["GEMINI_API_KEY"] = FAKE_KEY
    gc.urllib.request.urlopen = fake_urlopen
    gc.generate(None, "lis l'image", via="direct", image=tmp, json_mode=True)
    parts = SENT["body"]["contents"][0]["parts"]
    assert parts[1]["inline_data"]["mime_type"] == "image/png" and len(parts[1]["inline_data"]["data"]) > 100
    assert "systemInstruction" not in SENT["body"] and SENT["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_missing_key_fails_clearly_without_printing_anything_secret() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    try:
        gc.generate("s", "u", via="direct")
    except RuntimeError as e:
        assert "GEMINI_API_KEY" in str(e)
        return
    raise AssertionError("no error without a key")


def test_n8n_transport_posts_to_the_text_webhook() -> None:
    gc.urllib.request.urlopen = fake_urlopen
    gc.generate("système", "question", via="n8n", max_tokens=50)
    assert SENT["url"].endswith("/webhook/gemini-text-eval") and SENT["body"]["max_tokens"] == 50


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("gemini_client tests OK")
