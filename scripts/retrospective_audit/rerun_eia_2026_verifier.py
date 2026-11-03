"""Re-execute the frozen EIA CUDA verifier with an audit-only receipt."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT.parent / "shift-research-starter"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "EIA_2026_FULL_REPLAY.json"


def run() -> dict[str, object]:
    spec = importlib.util.spec_from_file_location(
        "frozen_eia_verifier", ROOT / "scripts" / "verify_eia_2026_reproducibility.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the frozen EIA verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ORIGINAL
    module.OUTPUT = ORIGINAL / "outputs/shiftguard_unified/independent_real_data/eia_2026_v1"
    module.ARCHIVE = ORIGINAL / "data/raw/eia/EBA.zip"
    module.READINESS = ORIGINAL / "data/reports/eia_2026_holdout_readiness.json"
    module.PROTOCOL = (
        ORIGINAL / "papers/shiftguard_unified/eia_2026_out_of_time_confirmation_protocol_v1.md"
    )
    module.RUNNER = ORIGINAL / "scripts/run_eia_2026_out_of_time_confirmation.py"
    module.AUDIT_SCRIPT = ORIGINAL / "scripts/audit_eia_2026_holdout_readiness.py"
    module.VERIFICATION = DEST
    if DEST.exists():
        raise FileExistsError(f"Audit receipt already exists: {DEST}")
    result = module.verify()
    if result["status"] != "passed_frozen_eia_2026_cuda_reproducibility_audit":
        raise AssertionError("Unexpected EIA verifier status")
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps({"status": result["status"], "rows": result["reproduced_dimensions"]}))
