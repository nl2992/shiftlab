"""Independent raw B3 arithmetic and paired bootstrap reconstruction; no new experiment."""

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results/b3"
OUTPUT = ROOT / "docs/retrospective_audit_2026_11_01/B3_EPISODE_RECOMPUTATION.json"


def reconstruct(rows, setting, rng):
    chosen = sorted((r for r in rows if r["setting"] == setting), key=lambda r: r["episode"])
    if not chosen or len({r["episode"] for r in chosen}) != len(chosen):
        raise ValueError("missing or duplicate episode")
    means = {}
    seeds = {}
    for policy in ("P0", "P1", "P2", "P3b", "P6"):
        raw = np.asarray([r["policies"][policy]["cost_seeds"] for r in chosen])
        stored = np.asarray([r["policies"][policy]["mean_cost"] for r in chosen])
        if not np.allclose(raw.mean(axis=1), stored, rtol=0, atol=1e-10):
            raise ValueError("seed/episode mean mismatch")
        means[policy] = raw.mean(axis=1)
        seeds[policy] = raw.mean(axis=0)
    paired = {}
    for rival in ("P0", "P2", "P1", "P6"):
        episode_diff = means["P3b"] - means[rival]
        low = len(chosen) < 5
        values = seeds["P3b"] - seeds[rival] if low else episode_diff
        draws = rng.integers(0, len(values), size=(2000, len(values)))
        lo, hi = np.percentile(values[draws].mean(axis=1), [2.5, 97.5])
        paired["P3b_minus_" + rival] = {
            "mean": float(episode_diff.mean()),
            "lo": float(lo),
            "hi": float(hi),
        }
    spend = 0.05 * np.mean([r["policies"]["P3b"]["mean_labels"] for r in chosen])
    return {
        "episodes": len(chosen),
        "mean_cost": {p: float(v.mean()) for p, v in means.items()},
        "paired": paired,
        "safe_bound": float(means["P0"].mean() * 1.02 + spend),
        "uncertainty_scope": "conditional query randomization on these fixed episodes"
        if len(chosen) < 5
        else "episode bootstrap; temporal independence not established",
    }


def main():
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    # Original RNG consumes streams in registered insertion order and settings in runner order.
    import re

    code = (ROOT / "scripts/promising_directions/b3_real_data.py").read_text(encoding="utf-8")
    seed = int(re.search(r"SEED_BASE\s*=\s*(\d+)", code).group(1))
    rng = np.random.default_rng(seed + 7)
    reports = {}
    for stream, stored in summary["streams"].items():
        path = SOURCE / (stream + ".jsonl")
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        settings = {"B200_cs5": stored["primary"], **stored["sensitivity"]}
        reports[stream] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "settings": {}}
        for setting, expected in settings.items():
            actual = reconstruct(rows, setting, rng)
            errors = []
            for policy, value in actual["mean_cost"].items():
                if abs(value - expected["mean_cost"][policy]) > 1e-9:
                    errors.append("mean " + policy)
            for rival, metrics in actual["paired"].items():
                for key, value in metrics.items():
                    if abs(value - expected["paired"][rival][key]) > 1e-9:
                        errors.append(rival + " " + key)
            actual["mismatches"] = errors
            reports[stream]["settings"][setting] = actual
    OUTPUT.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "streams": len(reports),
                "mismatches": sum(
                    len(x["mismatches"]) for s in reports.values() for x in s["settings"].values()
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
