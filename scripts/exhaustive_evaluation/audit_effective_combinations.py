"""Count mathematical algorithm identities and verify aliases on all saved paths."""

import json
from pathlib import Path

import numpy as np

from shiftlab.sota_search.bottleneck_round import bottleneck_combinations, effective_config_key

ROOT = Path(__file__).resolve().parents[2]


def main():
    configs = bottleneck_combinations()
    seen = {}
    aliases = []
    for i, c in enumerate(configs):
        key = effective_config_key(c)
        if key in seen:
            aliases.append((i, seen[key]))
        else:
            seen[key] = i
    reg = json.loads((ROOT / "docs/exhaustive_evaluation/round2_registration.json").read_text())
    for j, (kind, delay, ncal) in enumerate(reg["cases"]):
        name = f"{j:02d}_{kind}_d{delay}_cal{ncal}"
        with np.load(ROOT / f"outputs/exhaustive_evaluation/round2/{name}.npz") as data:
            for duplicate, canonical in aliases:
                for key in data.files:
                    np.testing.assert_array_equal(data[key][duplicate], data[key][canonical])
    result = {
        "registered_parameter_tuples": len(configs),
        "effective_distinct_round2": len(seen),
        "alias_count": len(aliases),
        "aliases": [{"alias": f"R2_{i:04d}", "canonical": f"R2_{k:04d}"} for i, k in aliases],
        "round1_distinct": 540,
        "total_effective_distinct": 540 + len(seen),
        "reason": "cost-floor guard is inactive when convex blend retains at least half of cost-only bet",
        "alias_arrays_equal_on_all_registered_cases": True,
    }
    (ROOT / "docs/exhaustive_evaluation/effective_combination_audit.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        "Effective distinct:",
        len(seen),
        "round2;",
        540 + len(seen),
        "total; aliases verified on every saved path",
    )


if __name__ == "__main__":
    main()
