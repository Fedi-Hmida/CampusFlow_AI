"""CF-015 / CF-017 — check that Qdrant holds exactly the chunks of data/index after WF-1, and write the ingestion log.

Per collection: point count = chunk count, the set of point ids = the set of uuid5 ids in the chunk file, every
payload has the required fields and the same article keys as its chunk, vector size 1024 / cosine.
Run after WF-1: .venv/Scripts/python -X utf8 scripts/index/verify_index.py [--run-seconds N]  → eval/retrieval/ingestion_log.md
"""
import argparse
import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QDRANT = "http://127.0.0.1:6333"
COLL = {"A": "regs_fixed", "B": "regs_structured"}
FIELDS = {"chunk_id", "strategy", "doc_id", "doc_title", "doc_status", "regime", "regimes", "article_keys", "page_start", "page_end", "text"}


def call(path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(QDRANT + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())["result"]


def scroll(coll: str) -> list[dict]:
    pts, offset = [], None
    while True:
        res = call(f"/collections/{coll}/points/scroll", {"limit": 256, "offset": offset, "with_payload": True, "with_vector": False})
        pts += res["points"]
        offset = res.get("next_page_offset")
        if not offset:
            return pts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-seconds", type=int)
    a = ap.parse_args()
    lines = ["# Ingestion log — WF-1 (CF-015 / CF-017)", "",
             f"Checked {date.today().isoformat()} by `scripts/index/verify_index.py` against `data/index/chunks_*.json`."
             + (f" WF-1 run time: {a.run_seconds // 60} min {a.run_seconds % 60} s (embedding on CPU, batches of 16)." if a.run_seconds else ""), "",
             "| Collection | Strategy | Chunks in file | Points in Qdrant | Same ids | Payload fields + keys | Vectors |", "|---|---|---:|---:|---|---|---|"]
    ok = True
    for s, coll in COLL.items():
        chunks = {c["point_id"]: c for c in json.loads((ROOT / f"data/index/chunks_{s}.json").read_text(encoding="utf-8"))}
        info = call(f"/collections/{coll}")
        pts = scroll(coll)
        ids = {p["id"] for p in pts}
        payload_ok = all(FIELDS <= set(p["payload"]) and p["payload"]["article_keys"] == chunks[p["id"]]["article_keys"]
                         for p in pts if p["id"] in chunks)
        v = info["config"]["params"]["vectors"]
        row_ok = len(pts) == len(chunks) and ids == set(chunks) and payload_ok and v["size"] == 1024 and v["distance"] == "Cosine"
        ok &= row_ok
        lines.append(f"| `{coll}` | {s} | {len(chunks)} | {len(pts)} | {'✅' if ids == set(chunks) else '❌'} | "
                     f"{'✅' if payload_ok else '❌'} | {v['size']} · {v['distance']} |")
    lines += ["", "**Result: " + ("OK — Qdrant matches the chunk files exactly.**" if ok else "MISMATCH — re-run WF-1.**")]
    (ROOT / "eval/retrieval/ingestion_log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
