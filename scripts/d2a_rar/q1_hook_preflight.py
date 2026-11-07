"""Stage-A preflight of the Q1 evidence identities against the new label-outcome seam (no Stage-B experiment is run).

Writes results/d2a_rar/q1_hook_preflight.json. 'eligible_now' = preflight ELIGIBLE and an implementation is registered in
shiftlab.bench.contract.evidence_q1 (before the seam, Stage B marked these NOT_IMPLEMENTED).
"""

from __future__ import annotations

import collections
import gzip
import json
from pathlib import Path

from shiftlab.autoresearch.preflight import preflight
from shiftlab.bench.contract.evidence_q1 import BLOCKED_VARIANTS, is_implemented, spec_for

ROOT = Path(__file__).resolve().parents[2]


def main() -> dict:
    with gzip.open(ROOT / "docs/d2a_rar/registry/CANDIDATE_REGISTRY.jsonl.gz", "rt") as f:
        reg = [json.loads(x) for x in f]
    with open(ROOT / "results/d2a_rar/stage_b/not_run.jsonl", encoding="utf8") as f:
        not_run = {json.loads(x)["candidate_id"] for x in f}
    rows = []
    for c in reg:
        if c["research_question"] != "Q1":
            continue
        v = preflight(c)
        impl = c["family"], c["variant"]
        implemented = impl not in BLOCKED_VARIANTS and is_implemented(
            {**c, "hook": "d2a.evidence_log_lik"}
        )
        rows.append({
            "candidate_id": c["candidate_id"], "host": c["host"], "family": c["family"], "variant": c["variant"],
            "target_null": c["target_null"], "prior_art_status": c["prior_art_status"], "role": c["role"],
            "in_stage_b_batch_001": c["in_stage_b_batch_001"], "was_not_implemented_in_stage_b": c["candidate_id"] in not_run,
            "preflight_status": v.status, "preflight_reasons": v.reasons, "implemented": implemented,
            "eligible_now": v.status == "ELIGIBLE" and implemented,
            "validity_claim": spec_for(c).validity if implemented else None,
        })  # fmt: skip
    d2a = [r for r in rows if r["host"] == "drift2act"]
    batch = [r for r in d2a if r["was_not_implemented_in_stage_b"]]
    summ = {
        "drift2act_q1_identities": len(d2a),
        "drift2act_eligible_now": sum(r["eligible_now"] for r in d2a),
        "batch001_not_implemented_identities": len(batch),
        "batch001_eligible_now": sum(r["eligible_now"] for r in batch),
        "contract_native_q1_identities": sum(r["host"] == "contract_native" for r in rows),
        "contract_native_eligible_now_via_promoter_shell": sum(r["eligible_now"] for r in rows if r["host"] == "contract_native"),
        "blocked": collections.Counter(r["preflight_status"] for r in d2a if not r["eligible_now"]),
        "validity_claims_batch001": collections.Counter(r["validity_claim"] for r in batch),
        "blocked_variants": {f"{a}.{b}": w for (a, b), w in BLOCKED_VARIANTS.items()},
    }  # fmt: skip
    out = {"summary": summ, "rows": rows}
    (ROOT / "results/d2a_rar/q1_hook_preflight.json").write_text(
        json.dumps(out, indent=1, default=dict), encoding="utf8"
    )
    return summ


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=dict))
