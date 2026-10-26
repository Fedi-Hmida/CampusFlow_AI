"""CF-010 — tests of the per-flow latency budget. Run: .venv/Scripts/python -X utf8 eval/latency/budget_test.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import budget as b  # noqa: E402

STEPS = {"router": {"seconds": 10.0, "kind": "measured"},
         "regulations": {"seconds": 60.0, "kind": "measured"},
         "tool": {"seconds": 1.0, "kind": "estimated"},
         "draft": {"prompt_tokens": 300, "output_tokens": 120, "kind": "derived"}}
RATES = {"prompt_tps": 30.0, "output_tps": 4.0}


def test_derived_step_uses_rates() -> None:
    assert b.step_seconds(STEPS["draft"], RATES) == 300 / 30.0 + 120 / 4.0


def test_flow_sums_steps_and_keeps_weakest_evidence() -> None:
    total, kind = b.flow_seconds(["router", "tool"], STEPS, RATES)
    assert total == 11.0 and kind == "estimated"
    total, kind = b.flow_seconds(["router", "regulations"], STEPS, RATES)
    assert total == 70.0 and kind == "measured"


def test_verdict_against_target() -> None:
    assert b.verdict(85.0, 90) == "within"
    assert b.verdict(95.0, 90) == "over"


def test_unknown_step_is_an_error() -> None:
    try:
        b.flow_seconds(["nope"], STEPS, RATES)
    except KeyError:
        return
    raise AssertionError("unknown step accepted")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("budget tests OK")
