"""Thin E4 runner: the frozen WP4 task on other EIA balancing authorities.

Imports the frozen WP4 modules UNCHANGED (``eia_paired_reserve``, ``eia_injected_harm``,
``eia_validity_analysis``, ``orientation_replay``). Only two things differ from WP4:

* the authority (the audit's reader is limited to CISO and ERCO, so an equivalent reader is
  used here), and
* the random-number streams, which come from seed block 100400001-100400999
  (``e4_split_and_orientation``) instead of the WP4 blocks 5920xxxx-5923xxxx. The coin functions
  of ``eia_validity_analysis`` are replaced at run time; the frozen file on disk is not edited.

Modes
-----
``smoke --authority ID``  runs the pipeline on ONE DEVELOPMENT authority. It refuses a locked
                          authority, and any id that is not in the development list.
``exposure-audit``        searches repository text for the eligible authority ids.
``locked``                refuses unless a protocol freeze record exists and the locked set has
                          not been opened; it is not authorised at the time of writing.

Seed layout (rank = index of the authority in the sorted eligible list; path index
``k = 2 * rank + w``, ``w = 0`` for 2025 and ``1`` for 2026; ``k < 110``):

    orientation null   100400001 + k                       (1,000 sign/uniform replicates)
    unmodified         100400111 + k                       (200 uniform replicates)
    injected harm      100400221 + 3 * k + o               (o = onset index; 200 replicates)
    single re-run      100400551 + (17 * k + j) mod 449    (j = registered cell index)

Run with ``uv run --no-sync python scripts/run_e4_heldout.py <mode> ...``.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import torch

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT, ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import audit_eia_2026_holdout_readiness as audit  # reused unchanged
import e4_eligibility as elig

from shiftlab.dive import eia_validity_analysis as eva
from shiftlab.dive.eia_paired_reserve import build_respondent_streams

STAGE1 = ROOT / "docs/research_refinement_v1/stage1"
OUT_ROOT = ROOT / "outputs/e4_heldout"
FREEZE_RECORD = STAGE1 / "P3_E4_freeze.json"  # written when the protocol is frozen
LOCKED_OPENED = STAGE1 / "e4_locked_opened.json"
REGION_MAP = STAGE1 / "e4_region_map.json"

SEED_NULL, SEED_UNMOD, SEED_INJ, SEED_RERUN = 100400001, 100400111, 100400221, 100400551
MAX_PATHS = 110
RERUN_SLOTS = 449
MIN_DISAGREEMENTS = 30  # registered informativeness threshold (obligation 4)
MIN_INFORMATIVE_PATHS = 6  # an arm's null is "supported" only with this many informative paths
MIN_INFORMATIVE_AUTHORITIES = 3  # ... drawn from at least this many authorities
ALPHA = 0.05
DELAY_ARRIVAL_HOURS = 24  # reference-training availability clock, from eia_paired_reserve

_HEAD = re.compile(rb'^\{"series_id"\s*:\s*"EBA\.([A-Z0-9]+)-ALL\.(D|DF|NG|TI)\.H"')


# ---------------------------------------------------------------------------------------------
# Seeds: replace the WP4 coin functions without editing the frozen module on disk.
# ---------------------------------------------------------------------------------------------
def _signs_uniforms(seed: int, n: int, reps: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    signs = 2 * rng.integers(0, 2, size=(reps, n)) - 1
    return signs, rng.random((reps, n))


def _check_k(k: int) -> int:
    if not 0 <= k < MAX_PATHS:
        raise ValueError(f"path index {k} outside the registered seed layout")
    return k


def install_e4_coins() -> None:
    eva.orientation_coins = lambda k, n, replicates=1000: _signs_uniforms(
        SEED_NULL + _check_k(k), n, replicates
    )
    eva.rerun_coins = lambda k, j, n, replicates=4000: _signs_uniforms(
        SEED_RERUN + (17 * _check_k(k) + j) % RERUN_SLOTS, n, replicates
    )
    eva.unmodified_coins = lambda k, n, replicates=200: np.random.default_rng(
        SEED_UNMOD + _check_k(k)
    ).random((replicates, n))
    eva.injection_coins = lambda k, o, n, replicates=200: np.random.default_rng(
        SEED_INJ + 3 * _check_k(k) + o
    ).random((replicates, n))


# ---------------------------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------------------------
def read_series(authorities: list[str]) -> dict:
    """Read the four series of each authority (same parsing as the audit's reader)."""
    if audit._sha256(audit.ARCHIVE) != audit.EXPECTED_SHA256:
        raise ValueError("EBA archive checksum mismatch")
    wanted = {(ba, k) for ba in authorities for k in audit.TYPES}
    series: dict[str, dict[int, float | None]] = {}
    with zipfile.ZipFile(audit.ARCHIVE) as zf:
        (member,) = [n for n in zf.namelist() if Path(n).name == "EBA.txt"]
        with zf.open(member) as source:
            for line in source:
                head = _HEAD.match(line)
                if head is None or (head.group(1).decode(), head.group(2).decode()) not in wanted:
                    continue
                item = json.loads(line)
                if item.get("f") != "H":
                    raise ValueError("expected hourly frequency")
                sid = item["series_id"]
                if sid in series:
                    raise ValueError(f"duplicate series {sid}")
                stamps = pd.to_datetime([p for p, _ in item["data"]], format="%Y%m%dT%H", utc=True)
                epochs = stamps.tz_convert(None).astype("datetime64[s]").astype("int64").tolist()
                values: dict[int, float | None] = {}
                for epoch, (_, raw) in zip(epochs, item["data"], strict=True):
                    if epoch in values:
                        raise ValueError(f"duplicate hour in {sid}")
                    values[epoch] = None if raw is None else float(raw)
                series[sid] = values
    missing = {f"EBA.{ba}-ALL.{k}.H" for ba, k in wanted} - set(series)
    if missing:
        raise ValueError(f"missing series: {sorted(missing)}")
    return series


def rank_of(ba: str, eligible: list[str]) -> int:
    return sorted(eligible).index(ba)


def authority_paths(streams: list, ba: str, rank: int) -> list[eva.PathData]:
    by_window = {s.window: s for s in streams}
    out = []
    for w, window in enumerate(("2025", "2026")):
        out.append(eva.PathData(2 * rank + w, by_window[window], by_window[eva.REHEARSAL]))
    return out


# ---------------------------------------------------------------------------------------------
# Registered summaries (E4 additions; they only read the analysis tables)
# ---------------------------------------------------------------------------------------------
def null_summary(null_df: pd.DataFrame, m_family: int) -> dict:
    """Bonferroni-adjusted exact bound on primary (epsilon = 0.1) cells and informativeness."""
    level = 1 - ALPHA / m_family
    primary = null_df[(null_df.epsilon == 0.1) & (null_df.stage == "original")].copy()
    rerun = null_df[(null_df.epsilon == 0.1) & (null_df.stage == "rerun")]
    key = ["path", "arm", "budget"]
    primary["budget"] = primary["budget"].fillna(-1.0)
    rerun = rerun.assign(budget=rerun["budget"].fillna(-1.0)).set_index(key)
    rows = []
    for _, r in primary.iterrows():
        x, n = int(r["alarms"]), int(r["replicates"])
        stage = "original"
        if (r["path"], r["arm"], r["budget"]) in rerun.index:
            rr = rerun.loc[(r["path"], r["arm"], r["budget"])]
            x, n, stage = int(rr["alarms"]), int(rr["replicates"]), "rerun"
        upper = eva.clopper_pearson_upper(x, n, level)
        rows.append(
            {
                "path": int(r["path"]),
                "arm": r["arm"],
                "budget": None if r["budget"] < 0 else float(r["budget"]),
                "disagreements": int(r["disagreements"]),
                "informative": bool(r["disagreements"] >= MIN_DISAGREEMENTS),
                "alarms": x,
                "replicates": n,
                "stage": stage,
                "bonferroni_upper": upper,
                "passes": bool(upper <= ALPHA),
            }
        )
    cells = pd.DataFrame(rows)
    return {
        "m_family": m_family,
        "level": level,
        "cells": cells,
        "arm_states": arm_states(cells),
        "all_pass": bool(cells["passes"].all()),
        "n_cells": len(cells),
        "n_informative_cells": int(cells["informative"].sum()),
        "n_failing": int((~cells["passes"]).sum()),
    }


def arm_states(cells: pd.DataFrame) -> dict:
    """H-B4(a) verdict per arm: FAIL, SUPPORTED, or INCONCLUSIVE (too few informative paths)."""
    out = {}
    for arm, part in cells.groupby("arm"):
        informative = part[part["informative"]]
        paths = sorted(set(informative["path"]))
        authorities = sorted({k // 2 for k in paths})
        if not part["passes"].all():
            state = "FAIL"
        elif (
            len(paths) >= MIN_INFORMATIVE_PATHS and len(authorities) >= MIN_INFORMATIVE_AUTHORITIES
        ):
            state = "SUPPORTED"
        else:
            state = "INCONCLUSIVE"
        out[arm] = {
            "state": state,
            "n_cells": len(part),
            "n_failing": int((~part["passes"]).sum()),
            "informative_paths": len(paths),
            "informative_authorities": len(authorities),
        }
    return out


def injected_summary(injected: pd.DataFrame) -> dict:
    """H-B4(b): fixed gating (r >= 0.05) against the full-feedback median delay.

    Detectable = the deterministic full-feedback monitor detects after onset (detection_rate 1).
    Match (primary, as WP4 compared them) = identical median delay in events.
    Secondary (descriptive) = median delay in hours within max(24 h, 10% of full feedback).
    """
    fb = injected[injected.arm == "full_feedback"].set_index(["path", "onset_fraction"])
    fixed = injected[(injected.arm == "gated_ht_fixed") & (injected.budget >= 0.05)]
    rows = []
    for _, r in fixed.iterrows():
        ref = fb.loc[(r["path"], r["onset_fraction"])]
        if ref["detection_rate"] != 1.0:
            continue
        tol = max(24.0, 0.1 * ref["median_delay_hours"])
        rows.append(
            {
                "path": int(r["path"]),
                "onset_fraction": float(r["onset_fraction"]),
                "budget": float(r["budget"]),
                "match_exact_events": bool(r["median_delay_events"] == ref["median_delay_events"]),
                "match_tolerance_hours": bool(
                    abs(r["median_delay_hours"] - ref["median_delay_hours"]) <= tol
                ),
            }
        )
    cells = pd.DataFrame(rows)
    out = {"cells": cells, "n_detectable_cells": len(cells)}
    for name in ("match_exact_events", "match_tolerance_hours"):
        out[name] = float(cells[name].mean()) if len(cells) else float("nan")
    return out


# ---------------------------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------------------------
def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def code_hashes() -> dict:
    files = [
        "scripts/run_e4_heldout.py",
        "scripts/e4_eligibility.py",
        "scripts/audit_eia_2026_holdout_readiness.py",
        "scripts/evaluate_eia_retraining_frontier.py",
        "src/shiftlab/dive/eia_paired_reserve.py",
        "src/shiftlab/dive/eia_injected_harm.py",
        "src/shiftlab/dive/eia_validity_analysis.py",
        "src/shiftlab/dive/orientation_replay.py",
        "src/shiftlab/dive/reserve_costs.py",
        "src/shiftlab/dive/gated_monitor_comparison.py",
        "src/shiftlab/dive/eprocess.py",
    ]
    return {f: audit._sha256(ROOT / f) for f in files}


def wp4_freeze_ok() -> bool:
    import verify_wp4_freeze

    return all(check.ok for check in verify_wp4_freeze.verify())


# ---------------------------------------------------------------------------------------------
# Core run
# ---------------------------------------------------------------------------------------------
def run_authorities(authorities: list[str], eligible: list[str], out_dir: Path, reps: dict) -> dict:
    """Streams, R20 check, and analyses (a)-(c) for the listed authorities."""
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out_dir}")
    if not wp4_freeze_ok():
        raise RuntimeError("WP4 freeze record does not verify; stop")
    install_e4_coins()
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    series = read_series(authorities)
    timings["read_series_s"] = time.perf_counter() - t0

    paths: list[eva.PathData] = []
    r20: dict[str, dict] = {}
    t0 = time.perf_counter()
    for ba in authorities:
        streams = build_respondent_streams(series, ba, torch.device("cpu"))
        rehearsal = next(s for s in streams if s.window == eva.REHEARSAL)
        procure = int(rehearsal.deployed_action.sum())
        ok = procure >= elig.MIN_REHEARSAL_PROCURE_EVENTS
        r20[ba] = {"rehearsal_procure_events": procure, "passes_R20": ok}
        if ok:
            paths.extend(authority_paths(streams, ba, rank_of(ba, eligible)))
    timings["build_streams_s"] = time.perf_counter() - t0

    result: dict = {"r20": r20, "paths": paths, "timings": timings}
    if not paths:
        return result
    t0 = time.perf_counter()
    null_df, decision = eva.null_analysis(paths, reps["null"], reps["rerun"])
    timings["null_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    unmodified = eva.unmodified_analysis(paths, reps["unmodified"])
    timings["unmodified_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    injected = eva.injected_analysis(paths, reps["injected"])
    timings["injected_s"] = time.perf_counter() - t0
    m_family = len(paths) * len(eva.registered_cells())
    result.update(
        null_df=null_df,
        decision=decision,
        unmodified=unmodified,
        injected=injected,
        null_summary=null_summary(null_df, m_family),
        injected_summary=injected_summary(injected),
    )
    return result


def smoke(authority: str, reps: dict) -> None:
    record = elig.load_eligibility()
    dev, locked = record["split"]["development"], record["split"]["locked"]
    if authority in locked:
        raise SystemExit(f"{authority} is a LOCKED authority; the smoke run never opens it")
    if authority not in dev:
        raise SystemExit(f"{authority} is not in the development list")
    out_dir = OUT_ROOT / f"smoke_{authority}"
    started = datetime.now(UTC).isoformat()
    t0 = time.perf_counter()
    result = run_authorities([authority], record["eligible"], out_dir, reps)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "mode": "smoke",
        "authority": authority,
        "split": "development",
        "replicates": reps,
        "started_utc": started,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "stage_seconds": {k: round(v, 1) for k, v in result["timings"].items()},
        "r20": result["r20"],
        "wp4_freeze_verified": True,
        "git_head": _git("rev-parse", "HEAD"),
        "code_sha256": code_hashes(),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
        },
        "device": "cpu",
        "command": " ".join(sys.argv),
    }
    if "null_summary" in result:
        ns, js = result["null_summary"], result["injected_summary"]
        result["null_df"].to_csv(out_dir / "null_cells.csv", index=False)
        ns["cells"].to_csv(out_dir / "null_bonferroni_cells.csv", index=False)
        result["unmodified"].to_csv(out_dir / "unmodified.csv", index=False)
        result["injected"].to_csv(out_dir / "injected.csv", index=False)
        js["cells"].to_csv(out_dir / "hb4b_cells.csv", index=False)
        summary["paths"] = [
            {
                "k": p.k,
                "window": p.stream.window,
                "n_events": p.n,
                "disagreements": int(np.asarray(p.stream.disagreement).sum()),
            }
            for p in result["paths"]
        ]
        summary["null"] = {
            "m_family": ns["m_family"],
            "level": ns["level"],
            "n_cells": ns["n_cells"],
            "n_informative_cells": ns["n_informative_cells"],
            "n_failing": ns["n_failing"],
            "all_pass": ns["all_pass"],
            "arm_states": ns["arm_states"],
            "wp4_style_decision": result["decision"]["null_passes"],
        }
        summary["hb4b"] = {
            "n_detectable_cells": js["n_detectable_cells"],
            "match_exact_events": js["match_exact_events"],
            "match_tolerance_hours": js["match_tolerance_hours"],
        }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: summary.get(k)
                for k in (
                    "authority",
                    "runtime_seconds",
                    "stage_seconds",
                    "r20",
                    "paths",
                    "null",
                    "hb4b",
                )
            },
            indent=2,
        )
    )


# ---------------------------------------------------------------------------------------------
# Exposure audit
# ---------------------------------------------------------------------------------------------
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".py",
    ".toml",
    ".log",
    ".jsonl",
    ".ini",
    ".cfg",
    ".tex",
    ".rst",
}
SCAN_ROOTS = ("outputs", "configs", "docs", "papers", "scripts", "src", "tests")
MAX_TEXT_BYTES = 200 * 1024 * 1024
MAX_PARQUET_BYTES = 300 * 1024 * 1024


def exposure_audit() -> Path:
    record = elig.load_eligibility()
    groups = {"locked": record["split"]["locked"], "development": record["split"]["development"]}
    all_ids = [i for g in groups.values() for i in g]
    alt = "|".join(sorted(map(re.escape, all_ids), key=len, reverse=True)).encode()
    token = re.compile(rb"(?<![A-Za-z0-9_])(" + alt + rb")(?![A-Za-z0-9_])")
    strict = re.compile(rb"EBA\.(" + alt + rb")-")
    hits: dict[str, dict] = {i: {"token_files": {}, "series_style_files": {}} for i in all_ids}
    skipped: dict[str, int] = {}
    scanned = {"text_files": 0, "parquet_files": 0}
    for top in SCAN_ROOTS:
        base = ROOT / top
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            suffix = path.suffix.lower()
            if suffix in TEXT_SUFFIXES:
                if path.stat().st_size > MAX_TEXT_BYTES:
                    skipped["text_too_large"] = skipped.get("text_too_large", 0) + 1
                    continue
                if rel.startswith("docs/research_refinement_v1/stage1/"):
                    continue  # this study's own registration files
                scanned["text_files"] += 1
                data = path.read_bytes()
                for m in token.finditer(data):
                    d = hits[m.group(1).decode()]["token_files"]
                    d[rel] = d.get(rel, 0) + 1
                for m in strict.finditer(data):
                    d = hits[m.group(1).decode()]["series_style_files"]
                    d[rel] = d.get(rel, 0) + 1
            elif suffix == ".parquet":
                if path.stat().st_size > MAX_PARQUET_BYTES:
                    skipped["parquet_too_large"] = skipped.get("parquet_too_large", 0) + 1
                    continue
                import pyarrow as pa
                import pyarrow.parquet as pq

                scanned["parquet_files"] += 1
                schema = pq.ParquetFile(path).schema_arrow
                cols = [
                    f.name
                    for f in schema
                    if pa.types.is_string(f.type) or pa.types.is_large_string(f.type)
                ]
                if not cols:
                    continue
                table = pq.read_table(path, columns=cols)
                for col in cols:
                    uniq = set(table.column(col).unique().to_pylist())
                    for ba in all_ids:
                        if ba in uniq:
                            d = hits[ba]["token_files"]
                            d[f"{rel}::{col}"] = 1
            else:
                skipped[suffix or "none"] = skipped.get(suffix or "none", 0) + 1
    report = {
        "artifact": "e4_exposure_audit",
        "run_utc": datetime.now(UTC).isoformat(),
        "scan_roots": list(SCAN_ROOTS),
        "excluded": "docs/research_refinement_v1/stage1/ (this registration)",
        "patterns": {
            "token": "case-sensitive id bounded by non-alphanumerics",
            "series_style": "EBA.<ID>-",
        },
        "scanned": scanned,
        "skipped_by_suffix": dict(sorted(skipped.items())),
        "groups": groups,
        "hits": {
            i: {
                "group": "locked" if i in groups["locked"] else "development",
                "token_file_count": len(v["token_files"]),
                "series_style_file_count": len(v["series_style_files"]),
                "token_files": dict(sorted(v["token_files"].items())),
                "series_style_files": dict(sorted(v["series_style_files"].items())),
            }
            for i, v in hits.items()
        },
        "interpretation_note": "Token hits can be incidental words or abbreviations; they are "
        "triaged by hand in P3_E4_protocol.md. Series-style hits are strong evidence of use.",
    }
    path = STAGE1 / "e4_exposure_audit.json"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------------------------
def locked() -> None:
    if not FREEZE_RECORD.is_file():
        raise SystemExit("locked mode refused: no protocol freeze record (P3_E4_freeze.json)")
    if LOCKED_OPENED.exists():
        raise SystemExit("locked mode refused: the locked set was already opened once")
    raise SystemExit("locked mode is not implemented in this commit; authorised after P3 freeze")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sm = sub.add_parser("smoke")
    sm.add_argument("--authority", required=True)
    sm.add_argument("--null-reps", type=int, default=1000)
    sm.add_argument("--rerun-reps", type=int, default=4000)
    sm.add_argument("--unmodified-reps", type=int, default=200)
    sm.add_argument("--injected-reps", type=int, default=200)
    sub.add_parser("exposure-audit")
    sub.add_parser("locked")
    args = parser.parse_args()
    if args.mode == "smoke":
        smoke(
            args.authority,
            {
                "null": args.null_reps,
                "rerun": args.rerun_reps,
                "unmodified": args.unmodified_reps,
                "injected": args.injected_reps,
            },
        )
    elif args.mode == "exposure-audit":
        print(exposure_audit().relative_to(ROOT).as_posix())
    else:
        locked()


if __name__ == "__main__":
    main()
