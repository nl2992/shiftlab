#!/usr/bin/env python3
"""Reweight fixed-cost P2/P3 trajectories to report P3 economics over switch costs."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/sprint2/P/p2p3/p2p3.json"
SWITCH_COSTS = (0.5, 2.0, 5.0, 20.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=Path("docs/sprint2/family_p/P3_cost_sweep.json"))
    args = parser.parse_args()
    source = args.source if args.source.is_absolute() else ROOT / args.source
    raw = json.loads(source.read_text())
    groups: dict[tuple[float, float, int], dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in raw["synthetic"]:
        key = (float(row["p"]), float(row["rho"]), int(row["delay"]))
        groups[key][str(row["policy"])].append(row)

    result_rows = []
    for (p, rho, delay), policies in sorted(groups.items()):
        seeds = sorted({int(row["seed"]) for rows in policies.values() for row in rows})
        for cs in SWITCH_COSTS:
            means = {}
            for policy, rows in policies.items():
                values = [float(r["net"]) + (cs - 5.0) * float(r["switches"]) for r in rows]
                means[policy] = sum(values) / len(values)
            p3 = means["P3_follow"]
            best_name = min((name for name in means if name != "P3_follow"), key=means.get)
            result_rows.append({
                "p": p, "rho": rho, "delay": delay, "switch_cost": cs,
                "n_seeds": len(seeds), "P3_follow_mean_J": p3,
                "best_other": best_name, "best_other_mean_J": means[best_name],
                "P3_minus_best_other": p3 - means[best_name],
                "best_policy": min(means, key=means.get),
                "policy_mean_J": means,
            })

    summary = {
        "source": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "switch_costs": list(SWITCH_COSTS),
        "reweighting": "J_cs = saved net cost at cs=5 + (cs-5) * saved deployment switches",
        "rows": result_rows,
        "limitations": [
            "This reweights the saved fixed-switch-cost trajectories; it does not rerun policies at each switch cost.",
            "It is valid for comparing realized cost under the same fixed action trajectories, not for policies whose actions adapt to switch cost.",
            "Development-only simulation evidence; best-other selection is descriptive and not selection-adjusted.",
        ],
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"rows": len(result_rows), "out": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
