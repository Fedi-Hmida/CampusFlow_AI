"""Phase 3 / CF-020 — run T1 against both Qdrant collections and score strategy A vs B.

For each T1 question: embed with bge-m3 (Ollama, same model as WF-1), query `regs_fixed` (A) and `regs_structured` (B),
top 10, in two modes:
  filtered    payload filter regimes ∈ question regime (what the bot does once it knows the regime; none for "all")
  unfiltered  no filter (regime unknown)
  official_first  regime filter + quota: top 3 official chunks and top 2 FICTITIOUS chunks, merged by score
              (added after the failure analysis: the FICTITIOUS absence procedure crowded out official articles)
Scores with eval/retrieval/retrieval_metrics.py at chunk level (k counts chunks — what the agent receives), k = 5 and 3.
Also: context size of the top-k, best score of answerable vs unanswerable questions (a "not found" threshold).
Outputs: eval/retrieval/rankings_T1.json (raw, re-scorable), eval/retrieval/results_T1.json, eval/retrieval/results_T1.md
Needs: Ollama + Qdrant running and WF-1 executed. Run: .venv/Scripts/python -X utf8 eval/retrieval/run_retrieval.py [--score-only]
"""
import argparse
import csv
import json
import statistics
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval/retrieval"))
import retrieval_metrics as rm  # noqa: E402

OLLAMA, QDRANT = "http://localhost:11434", "http://localhost:6333"
COLL = {"A": "regs_fixed", "B": "regs_structured"}
OUT = ROOT / "eval/retrieval"


def post(url: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def embed(texts: list[str]) -> list[list[float]]:
    return post(f"{OLLAMA}/api/embed", {"model": "bge-m3:567m", "input": texts})["embeddings"]


def search(strategy: str, vector: list[float], regime: str | None, limit: int = 10, status: str | None = None) -> list[dict]:
    body = {"query": vector, "limit": limit, "with_payload": ["chunk_id", "article_keys", "doc_id", "doc_status", "page_start", "text"]}
    must = []
    if regime and regime != "all":
        must.append({"key": "regimes", "match": {"any": regime.split(";")}})
    if status:
        must.append({"key": "doc_status", "match": {"value": status}})
    if must:
        body["filter"] = {"must": must}
    pts = post(f"{QDRANT}/collections/{COLL[strategy]}/points/query", body)["result"]["points"]
    return [{"chunk_id": p["payload"]["chunk_id"], "keys": p["payload"]["article_keys"], "doc_status": p["payload"]["doc_status"],
             "score": round(p["score"], 4), "chars": len(p["payload"]["text"])} for p in pts]


def official_first(strategy: str, vector: list[float], regime: str, n_official: int = 3, n_fictif: int = 2) -> list[dict]:
    """Quota retrieval: the best official chunks of the regime are always in the context, FICTITIOUS ones complete it."""
    merged = search(strategy, vector, regime, n_official, "official") + search(strategy, vector, regime, n_fictif, "FICTITIOUS")
    return sorted(merged, key=lambda c: -c["score"])


MODES = ("filtered", "unfiltered", "official_first")
VEC_CACHE = OUT / "question_vectors_T1.json"   # git-ignored: lets the modes be re-run without re-embedding


def run(rows: list[dict]) -> dict:
    if VEC_CACHE.exists():
        vecs = json.loads(VEC_CACHE.read_text(encoding="utf-8"))
    else:
        vecs = embed([r["question"] for r in rows])
        VEC_CACHE.write_text(json.dumps(vecs), encoding="utf-8")
    def one(s, mode, r, v):
        if mode == "official_first":
            return official_first(s, v, r["regime"])
        return search(s, v, r["regime"] if mode == "filtered" else None)
    return {s: {mode: {r["id"]: one(s, mode, r, v) for r, v in zip(rows, vecs)} for mode in MODES} for s in COLL}


def first_rank(expected: list[str], chunks: list[dict]) -> int | None:
    return next((i for i, c in enumerate(chunks, 1) if set(c["keys"]) & set(expected)), None)


def score(rows: list[dict], rk: dict) -> dict:
    res = {}
    for s in COLL:  # derived, no new query: 2 best official + 1 best FICTITIOUS chunk (the ADR-010 3-chunk budget)
        rk[s]["official_first_3"] = {rid: sorted([c for c in cs if c["doc_status"] == "official"][:2] +
                                                 [c for c in cs if c["doc_status"] == "FICTITIOUS"][:1], key=lambda c: -c["score"])
                                     for rid, cs in rk[s]["official_first"].items()}
    for s in COLL:
        for mode in MODES + ("official_first_3",):
            ranking = {rid: [c["keys"] for c in cs] for rid, cs in rk[s][mode].items()}
            m5, m3 = rm.evaluate_chunks(rows, ranking, 5), rm.evaluate_chunks(rows, ranking, 3)
            ans = [r for r in rows if r["answerable"] == "yes"]
            una = [r for r in rows if r["answerable"] == "no"]
            res[f"{s}/{mode}"] = {
                **m5, "hit@3": m3["hit@3"], "recall@3": m3["recall@3"],
                "context_chars_top5": int(statistics.mean(sum(c["chars"] for c in rk[s][mode][r["id"]][:5]) for r in rows)),
                "best_score_answerable": round(statistics.mean(rk[s][mode][r["id"]][0]["score"] for r in ans), 4),
                "best_score_unanswerable": round(statistics.mean(rk[s][mode][r["id"]][0]["score"] for r in una), 4),
                "min_best_score_answerable": min(rk[s][mode][r["id"]][0]["score"] for r in ans),
                "max_best_score_unanswerable": max(rk[s][mode][r["id"]][0]["score"] for r in una),
                "first_rank": {r["id"]: first_rank(rm.parse_expected(r["expected_article"]), rk[s][mode][r["id"]]) for r in ans},
            }
    return res


def markdown(rows: list[dict], res: dict) -> str:
    L = ["# T1 retrieval results — strategy A vs B (Phase 3, CF-020)", "",
         "Generated by `eval/retrieval/run_retrieval.py` (bge-m3, Qdrant cosine, top 10). Chunk-level metrics: k counts",
         f"retrieved chunks. {sum(r['answerable'] == 'yes' for r in rows)} answerable T1 questions are scored; "
         f"{sum(r['answerable'] == 'no' for r in rows)} unanswerable ones are used for the score threshold.", "",
         "| Strategy / mode | Hit@5 | Recall@5 | MRR | Hit@3 | Recall@3 | Context chars (top 5) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for k, v in res.items():
        L.append(f"| {k} | {v['hit@5']:.2f} | {v['recall@5']:.2f} | {v['mrr']:.2f} | {v['hit@3']:.2f} | {v['recall@3']:.2f} | {v['context_chars_top5']:,} |")
    L += ["", "## Best score: answerable vs unanswerable (« not found » threshold)", "",
          "| Strategy / mode | Mean best score (answerable) | Lowest (answerable) | Mean best score (unanswerable) | Highest (unanswerable) |",
          "|---|---:|---:|---:|---:|"]
    for k, v in res.items():
        L.append(f"| {k} | {v['best_score_answerable']} | {v['min_best_score_answerable']} | {v['best_score_unanswerable']} | {v['max_best_score_unanswerable']} |")
    L += ["", "## Rank of the first relevant chunk per question (— = not retrieved; official_first returns 5 chunks)", "",
          "| T1 | Regime | Topic | A filtered | B filtered | A official_first | B official_first |", "|---|---|---|---:|---:|---:|---:|"]
    for r in rows:
        if r["answerable"] == "yes":
            ranks = [res[f"{s}/{m}"]["first_rank"][r["id"]] for m in ("filtered", "official_first") for s in "AB"]
            L.append(f"| {r['id']} | {r['regime']} | {r['topic']} | " + " | ".join(str(x or "—") for x in ranks) + " |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(ROOT / "eval/testsets/T1_regulations.csv", encoding="utf-8")))
    if not a.score_only:
        (OUT / "rankings_T1.json").write_text(json.dumps(run(rows), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rk = json.loads((OUT / "rankings_T1.json").read_text(encoding="utf-8"))
    res = score(rows, rk)
    (OUT / "results_T1.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (OUT / "results_T1.md").write_text(markdown(rows, res), encoding="utf-8")
    for k, v in res.items():
        print(k, {m: (round(x, 3) if isinstance(x, float) else x) for m, x in v.items() if m != "first_rank"})


if __name__ == "__main__":
    main()
