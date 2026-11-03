"""Re-execute the archived Upworthy verifier, writing only an audit receipt."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT.parent / "shift-research-starter"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "UPWORTHY_FULL_REPLAY.json"


def run() -> dict[str, object]:
    spec = importlib.util.spec_from_file_location(
        "frozen_upworthy_verifier", ROOT / "scripts" / "verify_upworthy_policy.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the frozen verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ORIGINAL
    module.TRAIN = (
        ORIGINAL / "data/raw/upworthy/upworthy-archive-exploratory-packages-03.12.2020.csv"
    )
    module.HOLDOUT = ORIGINAL / "data/raw/upworthy/upworthy-archive-holdout-packages-03.12.2020.csv"
    module.PROTOCOL = (
        ORIGINAL / "papers/shiftguard_unified/upworthy_policy_selection_protocol_v1.md"
    )
    module.RUNNER = ORIGINAL / "scripts/evaluate_upworthy_policy.py"
    module.IMPLEMENTATION = ORIGINAL / "src/shiftlab/dive/upworthy_policy_selection.py"
    module.OUTPUT = ORIGINAL / "outputs/shiftguard_unified/real_data_development/upworthy_policy_v1"
    module.VERIFICATION = DEST
    if DEST.exists():
        raise FileExistsError(f"Audit receipt already exists: {DEST}")
    result = module.verify()
    if result["status"] != "passed_independent_full_reconstruction":
        raise AssertionError("Unexpected verifier status")
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps({"status": result["status"], "delta": result["reconstructed_delta_ctr"]}))
