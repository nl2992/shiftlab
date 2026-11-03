"""Metadata-only HGxH2c generator-key collision audit; no tensors or labels generated."""

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def seed_interval(base, key, count):
    h = int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big") & (2**30 - 1)
    start = base * 10_000_000_000 + h * 100_000
    return start, start + count - 1


def main():
    families = [
        "null_stationary",
        "null_boundary",
        "null_ar",
        "coshift",
        "cost_only",
        "pred_only",
        "opposed",
        "gradual",
        "intermittent",
        "lagged",
    ]
    keys = {}
    for T, mode in [(400, "smoke"), (2000, "full")]:
        for fam in families:
            for mag in (
                [0.0]
                if fam.startswith("null_")
                else ([0.16] if mode == "smoke" else [0.04, 0.08, 0.16])
            ):
                # World RNG ignores delay/regime/proxy intentionally; proxy RNG includes them.
                keys[(mode, "world", f"{fam}|{mag:g}|{T}")] = seed_interval(
                    90_000_000,
                    f"{fam}|{mag:g}|{T}",
                    1000 if mode == "smoke" or fam.startswith("null_") else 10000,
                )
                for delay, regime, proxy in itertools.product(
                    [0, 5, 20], ["full", "b20", "b05"], ["good", "biased", "noisy"]
                ):
                    key = f"{fam}|m{mag:g}|d{delay}|{regime}|{proxy}|T{T}"
                    keys[(mode, "proxy", key)] = seed_interval(
                        90_000_000,
                        key,
                        1000 if mode == "smoke" or fam.startswith("null_") else 10000,
                    )
    overlaps = []
    for (a, x), (b, y) in itertools.combinations(keys.items(), 2):
        if max(x[0], y[0]) <= min(x[1], y[1]):
            overlaps.append({"a": a, "b": b, "intersection": [max(x[0], y[0]), min(x[1], y[1])]})
    report = {
        "scope": "Generator-key integer intervals only, using current formula. Smoke superset checks all 27 delay/regime/proxy combinations, exceeding actual ten smoke cells. Does not prove stream independence or absence of hypothesis/design exposure. Code version parity with actual runs unresolved.",
        "keys_checked": len(keys),
        "unintended_interval_overlaps": overlaps,
        "intentional_reuse": "For fixed family/magnitude/T, world losses, onset and query uniforms are shared across delay, label regime and proxy quality; calibration shared across all cells. These cells are not independent source replicates.",
        "smoke_T": 400,
        "full_T": 2000,
        "smoke_full_seed_key_overlap_found": any(x["a"][0] != x["b"][0] for x in overlaps),
    }
    (ROOT / "docs/retrospective_audit_2026_11_01/HGXH2C_SEED_KEY_AUDIT.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "keys": len(keys),
                "unintended_overlaps": len(overlaps),
                "smoke_full_overlap": report["smoke_full_seed_key_overlap_found"],
            }
        )
    )


if __name__ == "__main__":
    main()
