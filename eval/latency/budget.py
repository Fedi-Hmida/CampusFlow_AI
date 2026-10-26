"""CF-010 — per-flow latency budget from the committed measurements (ADR-010).

Every step of a user flow gets a time and an evidence level:
  measured   mean of real calls (raw files below)
  derived    token budget × measured speed of the model (prompt tok/s, output tok/s)
  estimated  not measured (stated as such; e.g. n8n tool call)
A flow is as strong as its weakest step. Target: NFR-01, 90 s.
Inputs: eval/latency/results_2026-10-26.jsonl (CF-008b speeds), regulations_2026-10-26.jsonl, gemini_2026-10-26.jsonl,
        tuning_2026-10-26.jsonl, eval/agents/router_results/v2_few.json, eval/agents/vision_results/v4/*.json
Output: eval/latency/budget.md · Run: .venv/Scripts/python -X utf8 eval/latency/budget.py
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
L = ROOT / "eval/latency"
TARGET = 90
ORDER = {"measured": 0, "derived": 1, "estimated": 2}
FLOWS = {
    "Calendar question (« Quand est mon DS14 ? Je suis en 5DS6 »)": ["router", "tool"],
    "Contact / request (« À qui demander une attestation ? 4e année »)": ["router", "tool", "tool"],
    "Request + draft message": ["router", "tool", "draft"],
    "Regulation question (RAG)": ["router", "retrieval", "regulations", "checks"],
    "Photo + retake + draft (demo flow 2)": ["vision", "router", "retrieval", "regulations", "tool", "draft", "checks"],
    "Multi-topic (rule + date + office)": ["router", "retrieval", "regulations", "tool", "composer", "checks"],
}


def step_seconds(step: dict, rates: dict) -> float:
    if "seconds" in step:
        return step["seconds"]
    return step["prompt_tokens"] / rates["prompt_tps"] + step["output_tokens"] / rates["output_tps"]


def flow_seconds(names: list[str], steps: dict, rates: dict) -> tuple[float, str]:
    total = sum(step_seconds(steps[n], rates) for n in names)          # KeyError on an unknown step (tested)
    weakest = max((steps[n]["kind"] for n in names), key=ORDER.get)
    return round(total, 1), weakest


def verdict(seconds: float, target: int = TARGET) -> str:
    return "within" if seconds <= target else "over"


def jsonl(name: str) -> list[dict]:
    p = L / name
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def mean(xs) -> float:
    return round(statistics.mean(xs), 1)


def measurements() -> tuple[dict, dict, dict]:
    speed = next(r for r in jsonl("results_2026-10-26.jsonl") if "avg_prompt_tps" in r)
    rates = {"prompt_tps": speed["avg_prompt_tps"], "output_tps": speed["avg_output_tps"]}
    regs = jsonl("regulations_2026-10-26.jsonl")
    router = json.loads((ROOT / "eval/agents/router_results/v2_few.json").read_text(encoding="utf-8"))
    vision = [json.loads(p.read_text(encoding="utf-8"))["seconds"] for p in sorted((ROOT / "eval/agents/vision_results/v4").glob("T4-*.json"))]
    retr = [r for r in jsonl("tuning_2026-10-26.jsonl") if r.get("test") == "retrieval"]
    gem = jsonl("gemini_2026-10-26.jsonl")
    shared = {
        "tool": {"seconds": 1.0, "kind": "estimated", "note": "n8n sub-workflow + CSV lookup (not timed; node lookup < 10 ms)"},
        "checks": {"seconds": 0.1, "kind": "estimated", "note": "checks.js in n8n (node run < 50 ms)"},
        "vision": {"seconds": mean(vision), "kind": "measured", "note": f"Gemini Vision v4, {len(vision)} T4 images"},
        "retrieval": ({"seconds": mean(r["wall_s"] for r in retr), "kind": "measured", "note": f"bge-m3 embed + 2 Qdrant queries, {len(retr)} runs"}
                      if retr else {"seconds": 2.0, "kind": "estimated", "note": "embed + Qdrant (not timed)"}),
    }
    local = {**shared,
             # Ollama counters (model time): host wall times carry ~2 s of Windows localhost overhead per request
             "router": {"seconds": mean(v["prompt_s"] + v["output_s"] for v in router.values()), "kind": "measured",
                        "note": f"Router v2 few-shot, {len(router)} D5 rows, prefix cached"},
             "regulations": {"seconds": mean(r["prompt_s"] + r["output_s"] for r in regs), "kind": "measured",
                             "note": f"Regulations v2, {len(regs)} T1 questions, 5 chunks (≈ 2 100 tokens), ≤ 160 tokens out"},
             "draft": {"prompt_tokens": 600, "output_tokens": 120, "kind": "derived", "note": "600 in / 120 out"},
             "composer": {"prompt_tokens": 900, "output_tokens": 160, "kind": "derived", "note": "900 in / 160 out"}}
    g_router = [r["wall_s"] for r in gem if r["agent"] == "router"]
    g_regs = [r["wall_s"] for r in gem if r["agent"] == "regulations"]
    hybrid = {**shared,
              "router": {"seconds": mean(g_router), "kind": "measured", "note": f"Gemini Flash-Lite, {len(g_router)} calls (wall incl. n8n + ~2 s localhost)"},
              "regulations": {"seconds": mean(g_regs), "kind": "measured", "note": f"Gemini Flash-Lite, {len(g_regs)} calls (wall incl. n8n + ~2 s localhost)"},
              "draft": {"seconds": mean(g_regs), "kind": "estimated", "note": "as a Gemini Regulations call"},
              "composer": {"seconds": mean(g_regs), "kind": "estimated", "note": "as a Gemini Regulations call"}}
    return rates, local, hybrid


def main() -> None:
    rates, local, hybrid = measurements()
    out = ["# Latency budget per user flow (CF-010, ADR-010)", "",
           f"Target NFR-01: **{TARGET} s**. Local speeds (CF-008b): {rates['prompt_tps']} tok/s prompt, {rates['output_tps']} tok/s output.",
           "Generated by `eval/latency/budget.py` from the raw measurement files; *evidence* = weakest step of the flow.", "",
           "| Flow | Local 4B (option 1) | Evidence | Hybrid: Gemini text (option 2) | Evidence |", "|---|---:|---|---:|---|"]
    for name, steps in FLOWS.items():
        lt, lk = flow_seconds(steps, local, rates)
        ht, hk = flow_seconds(steps, hybrid, rates)
        out.append(f"| {name} | {lt} s {'✅' if verdict(lt) == 'within' else '❌'} | {lk} | {ht} s {'✅' if verdict(ht) == 'within' else '❌'} | {hk} |")
    out += ["", "## Steps", "", "| Step | Local | Hybrid | Basis (local / hybrid) |", "|---|---:|---:|---|"]
    for s in ["router", "retrieval", "regulations", "tool", "draft", "composer", "vision", "checks"]:
        out.append(f"| {s} | {round(step_seconds(local[s], rates), 1)} s | {round(step_seconds(hybrid[s], rates), 1)} s | "
                   f"{local[s]['kind']}: {local[s]['note']} / {hybrid[s]['kind']}: {hybrid[s]['note']} |")
    (L / "budget.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
