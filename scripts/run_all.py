"""Rebuild every Phase 1 output from data/raw/ in dependency order, then validate.

Run: .venv/Scripts/python scripts/run_all.py            (add --no-validate to skip the final check)
Each step is a separate script (see scripts/README.md); the run stops at the first failing step.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "scripts/corpus/extract_regs.py",            # raw regulations → cleaned JSON + official PDFs (no author metadata)
    "scripts/corpus/regenerate_fictif.py",       # FICTIF PDFs (labelled, CF-108b corrections, byte-reproducible)
    "scripts/corpus/extract_regs.py",            # re-extract the FICTITIOUS documents from their regenerated PDFs
    "scripts/corpus/build_consistency_review.py",
    "scripts/tables/transform_calendar.py",
    "scripts/tables/fix_directory.py",
    "scripts/tables/fix_requests.py",
    "scripts/tables/build_org_chart.py",
    "scripts/testsets/build_t1.py",
    "scripts/testsets/build_tests_t2_t5.py",
    "scripts/testsets/triage_d5.py",             # D5 candidates → status per row + Router dev labels (CF-208b)
]


def main() -> None:
    for step in STEPS:
        print(f"\n=== {step}", flush=True)
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / step)], cwd=ROOT)
        if r.returncode:
            sys.exit(f"step failed: {step}")
    if (ROOT / "eval/testsets/T4_photos/T4-02_convocation_sharp_source.png").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/testsets/degrade_t4.py")], cwd=ROOT, check=True)
    if "--no-validate" not in sys.argv:
        print("\n=== scripts/validate_data.py", flush=True)
        sys.exit(subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/validate_data.py")], cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
