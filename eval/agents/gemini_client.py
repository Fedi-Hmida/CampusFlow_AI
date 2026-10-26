"""CF-400 — one Gemini Flash-Lite client for the evaluation scripts, with two transports:

  via="n8n"     through the n8n credential on Fedi's laptop (workflows 00d_gemini_text_eval / 00c_vision_eval, published
                only for the run — n8n is public through ngrok); no key on the machine running the script.
  via="direct"  straight to the Gemini API with YOUR key in the environment variable GEMINI_API_KEY (set it in the
                shell, never in a file; the key is sent in a header, never in the URL, never printed).
Returns {text, seconds, prompt_tokens, output_tokens}. Retries on 429 / 5xx with backoff (free tier).
Tests: eval/agents/gemini_client_test.py
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "gemini-3.5-flash-lite"
API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
N8N = "http://127.0.0.1:5678/webhook"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _post(url: str, body: dict, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **(headers or {})})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.loads(r.read().decode())
            return out[0] if isinstance(out, list) else out
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503) or attempt == 3:
                raise RuntimeError(f"Gemini call failed: HTTP {e.code}") from None   # no URL / headers in the message
            time.sleep(15 * (attempt + 1))
    raise RuntimeError("unreachable")


def _parse(o: dict, t0: float) -> dict:
    u = o.get("usageMetadata", {})
    return {"text": o["candidates"][0]["content"]["parts"][0]["text"], "seconds": round(time.time() - t0, 2),
            "prompt_tokens": u.get("promptTokenCount"), "output_tokens": u.get("candidatesTokenCount")}


def generate(system: str | None, user: str, max_tokens: int = 200, temperature: float = 0.1, via: str = "n8n",
             image: Path | None = None, json_mode: bool = False) -> dict:
    t0 = time.time()
    if via == "direct":
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("set the environment variable GEMINI_API_KEY (your AI Studio key) — never put it in a file")
        parts = [{"text": user}]
        if image is not None:
            image = Path(image)
            parts.append({"inline_data": {"mime_type": MIME[image.suffix.lower()], "data": base64.b64encode(image.read_bytes()).decode()}})
        cfg = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if json_mode:
            cfg["responseMimeType"] = "application/json"
        body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": cfg}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return _parse(_post(API, body, {"x-goog-api-key": key}), t0)
    if via == "n8n":
        if image is not None:                           # 00c_vision_eval: one prompt + image, JSON mode, temperature 0
            image = Path(image)
            o = _post(f"{N8N}/vision-eval", {"prompt": user, "mime": MIME[image.suffix.lower()], "b64": base64.b64encode(image.read_bytes()).decode()})
        else:                                           # 00d_gemini_text_eval
            o = _post(f"{N8N}/gemini-text-eval", {"system": system or "", "user": user, "max_tokens": max_tokens})
        return _parse(o, t0)
    raise ValueError(f"unknown transport {via!r}")
