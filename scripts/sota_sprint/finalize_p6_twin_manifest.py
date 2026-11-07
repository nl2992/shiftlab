"""Validate complete P6 twin-bike records and reconstruct the completion manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import p6_twin_screen_cached as runner
import screen
from registry import IMPORT_ERRORS

OUT = runner.OUT
POLICIES = set(runner.POLICIES)
EPISODES = 120
SEEDS = 1000
EXPECTED = EPISODES * SEEDS * len(POLICIES)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    records = OUT / "records.jsonl"
    seen = {}
    policy_count = {p: 0 for p in POLICIES}
    rows = 0
    with records.open() as f:
        for lineno, line in enumerate(f, 1):
            r = json.loads(line)
            rows += 1
            ep = int(r["ep"])
            seed = int(r["seed"])
            pol = r["policy"]
            if (
                r.get("regime") != "twin_bike_hour"
                or pol not in POLICIES
                or not (0 <= ep < EPISODES)
                or not (0 <= seed < SEEDS)
            ):
                raise SystemExit(f"invalid record at line {lineno}: {r}")
            key = (ep, seed)
            policies = seen.setdefault(key, set())
            if pol in policies:
                raise SystemExit(f"duplicate policy row at line {lineno}: {key} {pol}")
            policies.add(pol)
            policy_count[pol] += 1
    expected_keys = {(ep, seed) for ep in range(EPISODES) for seed in range(SEEDS)}
    if (
        rows != EXPECTED
        or set(seen) != expected_keys
        or any(v != POLICIES for v in seen.values())
        or any(n != EPISODES * SEEDS for n in policy_count.values())
    ):
        raise SystemExit(
            f"incomplete coverage: rows={rows}/{EXPECTED}, keys={len(seen)}/{len(expected_keys)}, policies={policy_count}"
        )
    sources = runner._sources()
    sources[str(runner.DATA.relative_to(ROOT))] = sha256(runner.DATA)
    sources[str(records.relative_to(ROOT))] = sha256(records)
    receipt = {
        "manifest_reconstructed_after_run": True,
        "completion_verified": True,
        "audit_time_utc": datetime.now(UTC).isoformat(),
        "runner": str(Path(runner.__file__).relative_to(ROOT)),
        "runner_fix_after_simulation": "manifest-only: read IMPORT_ERRORS from registry, not screen; policy job and metrics unchanged",
        "actual_workers": runner.WORKERS,
        "seed_base": runner.SEED_BASE,
        "seeds_per_episode": SEEDS,
        "episodes": EPISODES,
        "policy_names": sorted(POLICIES),
        "observed_rows": rows,
        "expected_rows": EXPECTED,
        "unique_episode_seed_keys": len(seen),
        "rows_per_policy": policy_count,
        "contract": {**screen.CONTRACT, "alpha": runner.ALPHA},
        "git_revision": screen._git_rev(),
        "sources": sources,
        "import_errors": IMPORT_ERRORS,
        "cached_vs_uncached_smoke": "exact policy metric match excluding wall-clock runtime_s, episode 3 seed 17",
        "runtime_seconds": None,
        "runtime_note": "not recorded because original completion-manifest write failed; not reconstructed",
    }
    (OUT / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in [
                    "manifest_reconstructed_after_run",
                    "completion_verified",
                    "observed_rows",
                    "expected_rows",
                    "unique_episode_seed_keys",
                    "rows_per_policy",
                    "runtime_seconds",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
