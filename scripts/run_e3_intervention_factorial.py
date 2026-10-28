"""Run the E3 matched-opportunity intervention factorial (protocol P2).

Every seed is replayed through every cell (onset x coverage x rollback x reference
state x response), so seeds map to cells one-to-one-to-all and every stream is
analysed, including no-alarm streams.

  uv run --no-sync python scripts/run_e3_intervention_factorial.py \
      --block dev --n-per-cell 40 --out outputs/e3/dev_smoke --workers 8 --device cpu

The confirmation block refuses to run without a freeze record whose protocol hash
matches the protocol document. CUDA is not supported (and not needed on CPU).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import e3_intervention_factorial as e3
from shiftlab.seed_registry import load_registry

BLOCK_IDS = {"dev": "e3_dev_smoke", "confirmation": "e3_confirmation"}
PROTOCOL = ROOT / "docs/research_refinement_v1/stage1/P2_E3_protocol.md"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def config_dict(shift: float) -> dict[str, object]:
    return {
        "onsets": e3.ONSETS,
        "coverage_end": e3.COVERAGE_END,
        "rollbacks": list(e3.ROLLBACKS),
        "reference_states": list(e3.REFERENCE_STATES),
        "responses": list(e3.RESPONSES),
        "deterioration_lag": e3.DETERIORATION_LAG,
        "deterioration_shift": shift,
        "cert_window": e3.CERT_WINDOW,
        "monitor_rate": e3.MONITOR_QUERY_RATE,
        "cert_label_cap": e3.SCOUT_CERT_LABEL_CAP,
        "rollback_label_cap": e3.ROLLBACK_LABEL_CAP,
        "rollback_rate": e3.QUERY_RATE,
        "alphas": {
            "monitor": e3.MONITOR_ALPHA,
            "promotion": e3.PROMOTION_ALPHA,
            "rollback": e3.ROLLBACK_ALPHA,
        },
        "switch_cost": e3.SWITCH_COST,
        "rollback_cost": e3.ROLLBACK_COST,
        "harm_margin": e3.HARM_MARGIN,
        "deploy_rule": "window_end",
        "n_events": e3.N_EVENTS,
    }


def _work(args: tuple[int, str, float]) -> list[dict[str, object]]:
    seed, device, shift = args
    return e3.run_stream(seed, device=device, shift=shift)  # type: ignore[return-value]


def check_freeze(record: Path | None) -> dict[str, object]:
    if record is None or not record.is_file():
        raise SystemExit("confirmation block requires --freeze-record (protocol freeze record)")
    data = json.loads(record.read_text(encoding="utf-8"))
    expected = _sha256_file(PROTOCOL)
    if data.get("protocol_sha256") != expected:
        raise SystemExit("freeze record protocol_sha256 does not match the protocol document")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", choices=tuple(BLOCK_IDS), required=True)
    parser.add_argument(
        "--n-per-cell", type=int, required=True, help="seeds (each seed enters every cell)"
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--device", choices=("cpu",), default="cpu")
    parser.add_argument(
        "--shift",
        type=float,
        default=e3.DETERIORATION_SHIFT,
        help="deterioration shift; non-default values are development sensitivity only",
    )
    parser.add_argument("--freeze-record", type=Path, default=None)
    args = parser.parse_args()

    block = next(b for b in load_registry().blocks if b.id == BLOCK_IDS[args.block])
    capacity = block.end - block.start + 1
    if not 1 <= args.n_per_cell <= capacity:
        raise SystemExit(f"--n-per-cell must lie in [1, {capacity}] for block {block.id}")
    if args.block == "confirmation" and args.shift != e3.DETERIORATION_SHIFT:
        raise SystemExit("confirmation must use the registered deterioration shift")
    freeze = check_freeze(args.freeze_record) if args.block == "confirmation" else None
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory {out}")

    seeds = list(range(block.start, block.start + args.n_per_cell))
    started = time.time()
    done_rows: dict[int, list[dict[str, object]]] = {}
    if args.workers > 1:
        try:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(_work, (s, args.device, args.shift)): s for s in seeds}
                for future in as_completed(futures):
                    done_rows[futures[future]] = future.result()
                    if len(done_rows) % 10 == 0:
                        print(
                            f"{len(done_rows)}/{len(seeds)} seeds, {time.time() - started:.0f}s",
                            flush=True,
                        )
        except BrokenProcessPool:
            print(
                "worker pool died (likely memory); finishing remaining seeds sequentially",
                flush=True,
            )
    for seed in seeds:
        if seed not in done_rows:
            done_rows[seed] = _work((seed, args.device, args.shift))
            if len(done_rows) % 10 == 0:
                print(
                    f"{len(done_rows)}/{len(seeds)} seeds, {time.time() - started:.0f}s", flush=True
                )
    frames = [pd.DataFrame(done_rows[s]) for s in seeds]
    detail = pd.concat(frames, ignore_index=True)
    expected_rows = len(seeds) * len(e3.all_cells()) * len(e3.RESPONSES)
    if len(detail) != expected_rows:
        raise RuntimeError(f"row count {len(detail)} != expected {expected_rows}")
    path = out / "e3_rows.parquet"
    detail.to_parquet(path, index=False)
    cfg = config_dict(args.shift)
    cfg_sha = _sha256_bytes(json.dumps(cfg, sort_keys=True).encode("utf-8"))
    source_files = [
        ROOT / "src/shiftlab/dive/e3_intervention_factorial.py",
        ROOT / "src/shiftlab/dive/integrated_pipeline.py",
        ROOT / "src/shiftlab/dive/budgeted_promotion.py",
        ROOT / "src/shiftlab/dive/eprocess.py",
        Path(__file__),
    ]
    manifest = {
        "experiment": "e3_matched_opportunity_intervention_factorial",
        "block": args.block,
        "registry_block": block.id,
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "n_seeds": len(seeds),
        "rows": len(detail),
        "status": ("development_only_not_confirmatory" if args.block == "dev" else "confirmation"),
        "device": args.device,
        "workers": args.workers,
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime_seconds": time.time() - started,
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "config": cfg,
        "config_sha256": cfg_sha,
        "protocol_sha256": _sha256_file(PROTOCOL) if PROTOCOL.is_file() else None,
        "freeze_record": freeze,
        "source_sha256": {str(p.relative_to(ROOT)): _sha256_file(p) for p in source_files},
        "rows_sha256": _sha256_file(path),
        "seed_cell_mapping": "every seed enters every cell and response; seeds are paired",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {path.name} in {out.name} ({len(detail)} rows, {time.time() - started:.0f}s)")


if __name__ == "__main__":
    main()
