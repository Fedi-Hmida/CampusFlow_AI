"""Retrieval metrics for T1 (Phase 3). `expected` is the T1 expected_article field: article keys separated by "|".

hit_at_k    1 if at least one expected key is in the top k, else 0
recall_at_k share of the expected keys found in the top k
mrr         1 / rank of the first expected key in the ranking (0 if absent)
Unanswerable rows (empty expected) are excluded from the averages and evaluated separately (expected: "not found").
"""


def parse_expected(expected: str) -> list[str]:
    return [k for k in (expected or "").split("|") if k]


def hit_at_k(expected: list[str], retrieved: list[str], k: int = 5) -> float:
    return float(any(r in expected for r in retrieved[:k]))


def recall_at_k(expected: list[str], retrieved: list[str], k: int = 5) -> float:
    return len(set(expected) & set(retrieved[:k])) / len(set(expected)) if expected else 0.0


def mrr(expected: list[str], retrieved: list[str]) -> float:
    return next((1.0 / i for i, r in enumerate(retrieved, 1) if r in expected), 0.0)


def evaluate(rows: list[dict], ranking: dict[str, list[str]], k: int = 5) -> dict:
    """rows: T1 rows (dicts); ranking: {row id: retrieved article keys, best first}."""
    scored = [r for r in rows if parse_expected(r["expected_article"])]
    if not scored:
        return {"n": 0}
    h = [hit_at_k(parse_expected(r["expected_article"]), ranking.get(r["id"], []), k) for r in scored]
    rc = [recall_at_k(parse_expected(r["expected_article"]), ranking.get(r["id"], []), k) for r in scored]
    m = [mrr(parse_expected(r["expected_article"]), ranking.get(r["id"], [])) for r in scored]
    n = len(scored)
    return {"n": n, f"hit@{k}": sum(h) / n, f"recall@{k}": sum(rc) / n, "mrr": sum(m) / n}


def self_test() -> None:
    exp = parse_expected("A|B")
    assert hit_at_k(exp, ["x", "B", "y"]) == 1.0 and hit_at_k(exp, ["x", "y"]) == 0.0
    assert recall_at_k(exp, ["A", "x", "B"]) == 1.0 and recall_at_k(exp, ["A", "x"]) == 0.5
    assert mrr(exp, ["x", "x", "B"]) == 1 / 3 and mrr(exp, ["x"]) == 0.0
    assert hit_at_k(exp, ["x"] * 5 + ["A"]) == 0.0  # beyond k
    r = evaluate([{"id": "1", "expected_article": "A|B"}, {"id": "2", "expected_article": "C"}, {"id": "3", "expected_article": ""}],
                 {"1": ["B", "A"], "2": ["x", "C"]})
    assert r == {"n": 2, "hit@5": 1.0, "recall@5": 1.0, "mrr": 0.75}, r


if __name__ == "__main__":
    self_test()
    print("retrieval_metrics self-test OK")
