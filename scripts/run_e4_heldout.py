"""E4 runner: the frozen WP4 task on other EIA balancing authorities, as a NEW E4 composition.

The frozen WP4 modules (``eia_paired_reserve``, ``eia_injected_harm``, ``eia_validity_analysis``,
``orientation_replay``) are imported without edits. The effective program is nevertheless a new
composition, and the freeze record must list this file, the replacements below and every imported
module (``freeze-list`` prints them). The composition differs from WP4 in these ways:

* an equivalent series reader for any authority (the audit's reader is fixed to CISO and ERCO);
* the coin functions ``orientation_coins``, ``unmodified_coins`` and ``injection_coins`` of
  ``eia_validity_analysis`` are replaced at run time (seed block 100400001-100400999). The WP4
  re-run coin function is not used: E4 has no re-run;
* the null loop is E4's own (``e4_null_analysis``): a FIXED replication count per cell, no
  data-dependent re-run, and no unadjusted-95% trigger;
* E4 summaries: Bonferroni across the registered family, arm/budget information, q-stratified
  H-B4(b), regional clusters.

Modes
-----
``smoke --authority ID``  one DEVELOPMENT authority; refuses locked and unknown ids.
``exposure-audit``        searches the repository for the eligible authority ids.
``freeze-list``           prints the files the freeze record must list.
``locked``                requires ``shiftlab.freeze.require_freeze`` on the P3 freeze record, then
                          creates an exclusive one-opening marker BEFORE reading any locked value.

Seed layout (rank = index of the authority in the sorted eligible list; path index
``k = 2 * rank + w``, ``w = 0`` for 2025 and ``1`` for 2026; ``k < 110``):

    orientation null   100400001 + k          (1,000 sign/uniform replicates; fixed, no re-run)
    unmodified         100400111 + k          (200 uniform replicates)
    injected harm      100400221 + 3 * k + o  (o = onset index; 200 replicates)
    100400551-100400999 are reserved and unused (the WP4-style re-run is dropped).

Run with ``uv run --no-sync python scripts/run_e4_heldout.py <mode> ...``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
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

import audit_eia_2026_holdout_readiness as audit  # reused unchanged  # noqa: E402 -- local script path bootstrap
import e4_eligibility as elig  # noqa: E402 -- local script path bootstrap

from shiftlab import freeze  # noqa: E402 -- local script path bootstrap
from shiftlab.dive import eia_validity_analysis as eva  # noqa: E402 -- local script path bootstrap
from shiftlab.dive.eia_paired_reserve import build_respondent_streams  # noqa: E402 -- local script path bootstrap
from shiftlab.dive.gated_monitor_comparison import DisagreementPacer  # noqa: E402 -- local script path bootstrap
from shiftlab.dive.orientation_replay import _propensity_path  # noqa: E402 -- local script path bootstrap

STAGE1 = ROOT / "docs/research_refinement_v1/stage1"
OUT_ROOT = ROOT / "outputs/e4_heldout"
FREEZE_RECORD = STAGE1 / "P3_E4_freeze.json"  # written by the lead when the protocol is frozen
REGION_MAP = STAGE1 / "e4_region_map.json"
PROTOCOL_REL = "docs/research_refinement_v1/stage1/P3_E4_protocol.md"
# The freeze record must list at least these (locked mode refuses otherwise).
REQUIRED_FROZEN = (
    PROTOCOL_REL,
    "scripts/run_e4_heldout.py",
    "scripts/e4_eligibility.py",
    "docs/research_refinement_v1/stage1/e4_eligibility.json",
    "docs/research_refinement_v1/stage1/e4_region_map.json",
    "src/shiftlab/dive/eia_validity_analysis.py",
    "src/shiftlab/dive/orientation_replay.py",
)

SEED_NULL, SEED_UNMOD, SEED_INJ = 100400001, 100400111, 100400221
MAX_PATHS = 110
ALPHA = 0.05
REPLICATES = {"null": 1000, "unmodified": 200, "injected": 200}  # registered, fixed
MAX_AUTHORITIES_LOCKED = 21
MAX_FAMILY_CELLS = 2 * MAX_AUTHORITIES_LOCKED * 17  # 714
# Information screens (registered; engineering choices, see the protocol)
MIN_DISAGREEMENTS = 30  # path screen
MIN_EXPECTED_QUERIED = 8  # cell screen: 8 queried +5 events are needed for any alarm
MIN_INFORMATIVE_PATHS = 6  # null "supported" needs this many arm-informative paths ...
MIN_INFORMATIVE_AUTHORITIES = 3  # ... from at least this many authorities
MIN_HB4B_CELLS = 10  # H-B4(b) decided only with this many detectable q<1 cells ...
MIN_HB4B_AUTHORITIES = 3  # ... from at least this many authorities
HB4B_MATCH_FRACTION = 0.80

_HEAD = re.compile(rb'^\{"series_id"\s*:\s*"EBA\.([A-Z0-9]+)-ALL\.(D|DF|NG|TI)\.H"')


def min_zero_alarm_replicates(m_family: int, alpha: float = ALPHA) -> int:
    """Smallest R such that 0 alarms in R replicates certifies <= alpha at Bonferroni level."""
    return math.ceil(math.log(m_family / alpha) / -math.log(1 - alpha))


# ---------------------------------------------------------------------------------------------
# Seeds: replace the WP4 coin functions without editing the frozen module on disk.
# ---------------------------------------------------------------------------------------------
REPLACED_NAMES = ("orientation_coins", "unmodified_coins", "injection_coins")


def _signs_uniforms(seed: int, n: int, reps: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    signs = 2 * rng.integers(0, 2, size=(reps, n)) - 1
    return signs, rng.random((reps, n))


def _check_k(k: int) -> int:
    if not 0 <= k < MAX_PATHS:
        raise ValueError(f"path index {k} outside the registered seed layout")
    return k


def e4_orientation_coins(k: int, n: int, replicates: int = 1000):
    return _signs_uniforms(SEED_NULL + _check_k(k), n, replicates)


def e4_unmodified_coins(k: int, n: int, replicates: int = 200):
    return np.random.default_rng(SEED_UNMOD + _check_k(k)).random((replicates, n))


def e4_injection_coins(k: int, o: int, n: int, replicates: int = 200):
    if not 0 <= o <= 2:
        raise ValueError("onset index must be 0, 1 or 2")
    return np.random.default_rng(SEED_INJ + 3 * _check_k(k) + o).random((replicates, n))


def install_e4_coins() -> tuple[str, ...]:
    """Replace exactly ``REPLACED_NAMES`` in ``eia_validity_analysis``; return the names."""
    eva.orientation_coins = e4_orientation_coins
    eva.unmodified_coins = e4_unmodified_coins
    eva.injection_coins = e4_injection_coins
    return REPLACED_NAMES


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
# E4 null loop: fixed replication count, no re-run
# ---------------------------------------------------------------------------------------------
def cell_information(
    p: eva.PathData, arm: str, budget: float | None, processed: np.ndarray
) -> float:
    """Expected queried disagreements over the PROCESSED prefix (arm/budget-specific).

    ``processed[r]`` is the number of events replicate r processes before the reserve stop. Whether
    event t is processed depends only on coins at events before t, and the query coin at t is
    independent of that, so the expected queried disagreements are
    ``sum_t D_t q_t P(t is processed)``, with ``P`` estimated from the null replicates of the arm's
    own coin stream. Disagreements after the reserve is exhausted therefore do not count.
    """
    active = np.asarray(p.stream.disagreement, dtype=bool)
    n = len(active)
    proc = np.asarray(processed)
    alive = (proc[:, None] > np.arange(n)[None, :]).mean(axis=0)  # P(event t processed)
    if arm == "full_feedback":
        q = np.ones(n)
    elif arm == "ungated_ht":
        q = np.full(n, float(budget))
    else:
        q, _ = _propensity_path(
            arm, active, p.tariffs, p.validation_disagreement, p.validation_tariffs, float(budget)
        )
        q = np.asarray(q)
    return float((active * q * alive).sum())


def fixed_propensity(p: eva.PathData, budget: float) -> float:
    return float(DisagreementPacer(p.validation_disagreement, p.validation_tariffs, budget).fixed)


def e4_null_analysis(paths: list[eva.PathData], replicates: int) -> pd.DataFrame:
    """Orientation null for every registered cell, both epsilons, ONE look, no re-run."""
    rows = []
    for p in paths:
        signs, uniforms = eva.orientation_coins(p.k, p.n, replicates)
        for j, (arm, budget) in enumerate(eva.registered_cells()):
            fb = arm == "full_feedback"
            batches = {}
            for eps in eva.EPSILONS:
                batches[eps] = eva._replay(
                    p,
                    arm,
                    budget,
                    paired_cost=p.stream.paired_cost,
                    disagreement=p.stream.disagreement,
                    signs=signs,
                    uniforms=None if fb else uniforms,
                    epsilon=eps,
                )
            # the reserve stop depends on queries only, so both epsilons share it
            info = cell_information(p, arm, budget, batches[eva.EPSILONS[0]].processed)
            for eps, batch in batches.items():
                row = eva._null_row(p, arm, budget, eps, batch, "fixed")
                row["cell_index"] = j
                row["expected_queried_disagreements"] = info
                rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------
# Registered summaries (read the analysis tables only)
# ---------------------------------------------------------------------------------------------
def null_summary(null_df: pd.DataFrame, m_family: int, replicates: int) -> dict:
    """Bonferroni exact bound per primary cell (epsilon = 0.1). One look, no re-run.

    A bound above 0.05 means INSUFFICIENT validation for the cell. It is not a demonstration that
    the monitor is invalid; ``point_exceeds_alpha`` flags the stronger case.
    """
    primary = null_df[null_df.epsilon == 0.1].copy()
    if len(primary) != m_family:
        raise ValueError(f"family size {len(primary)} differs from the registered m = {m_family}")
    need = min_zero_alarm_replicates(m_family)
    if replicates < need:
        raise ValueError(f"{replicates} replicates cannot certify 0 alarms at m = {m_family}")
    level = 1 - ALPHA / m_family
    rows = []
    for _, r in primary.iterrows():
        x, n = int(r["alarms"]), int(r["replicates"])
        upper = eva.clopper_pearson_upper(x, n, level)
        d = int(r["disagreements"])
        info = float(r["expected_queried_disagreements"])
        rows.append(
            {
                "path": int(r["path"]),
                "arm": r["arm"],
                "budget": None if pd.isna(r["budget"]) else float(r["budget"]),
                "disagreements": d,
                "expected_queried_disagreements": info,
                "mean_labels": float(r["mean_labels"]),
                "informative": bool(d >= MIN_DISAGREEMENTS and info >= MIN_EXPECTED_QUERIED),
                "alarms": x,
                "replicates": n,
                "bonferroni_upper": upper,
                "passes": bool(upper <= ALPHA),
                "point_exceeds_alpha": bool(x / n > ALPHA),
            }
        )
    cells = pd.DataFrame(rows)
    return {
        "m_family": m_family,
        "level": level,
        "min_zero_alarm_replicates": need,
        "cells": cells,
        "arm_states": arm_states(cells),
        "all_validated": bool(cells["passes"].all()),
        "n_cells": len(cells),
        "n_informative_cells": int(cells["informative"].sum()),
        "n_insufficient": int((~cells["passes"]).sum()),
    }


def arm_states(cells: pd.DataFrame) -> dict:
    """H-B4(a) per arm: NOT_VALIDATED, SUPPORTED or INCONCLUSIVE.

    An arm-informative path has an informative cell at the arm's largest budget (the cell with
    the most information); full feedback has a single cell per path. NOT_VALIDATED is a validity
    stop for the arm's efficiency claims (insufficient validation, not proved invalid).
    """
    out = {}
    if cells.empty:
        return out
    for arm, part in cells.groupby("arm"):
        top = part if part["budget"].isna().all() else part[part["budget"] == part["budget"].max()]
        paths = sorted(set(top[top["informative"]]["path"]))
        authorities = sorted({k // 2 for k in paths})
        if not part["passes"].all():
            state = "NOT_VALIDATED"
        elif (
            len(paths) >= MIN_INFORMATIVE_PATHS and len(authorities) >= MIN_INFORMATIVE_AUTHORITIES
        ):
            state = "SUPPORTED"
        else:
            state = "INCONCLUSIVE"
        out[str(arm)] = {
            "state": state,
            "n_cells": len(part),
            "n_insufficient": int((~part["passes"]).sum()),
            "n_point_exceeds_alpha": int(part["point_exceeds_alpha"].sum()),
            "informative_paths": len(paths),
            "informative_authorities": len(authorities),
        }
    return out


def injected_summary(injected: pd.DataFrame, paths: list[eva.PathData]) -> dict:
    """H-B4(b), stratified by the fixed propensity q of the gated_ht_fixed arm.

    Detectable = full feedback alarms at or after onset. Match (primary, as WP4) = identical
    median delay in events. Secondary = median delay in hours within max(24 h, 10%).
    Cells with q = 1 are STRUCTURAL (fixed gating labels every disagreement): they are reported
    but never count toward support. The criterion is evaluated on the q < 1 stratum only.
    """
    by_k = {p.k: p for p in paths}
    columns = [
        "path",
        "onset_fraction",
        "budget",
        "q_fixed",
        "stratum",
        "match_exact_events",
        "match_tolerance_hours",
    ]
    if injected.empty:
        return {
            "cells": pd.DataFrame(columns=columns),
            "n_detectable_cells": 0,
            "strata": {},
            "state": "INCONCLUSIVE",
        }
    fb = injected[injected.arm == "full_feedback"].set_index(["path", "onset_fraction"])
    fixed = injected[(injected.arm == "gated_ht_fixed") & (injected.budget >= 0.05)]
    rows = []
    for _, r in fixed.iterrows():
        ref = fb.loc[(r["path"], r["onset_fraction"])]
        if ref["detection_rate"] != 1.0:
            continue
        q = fixed_propensity(by_k[int(r["path"])], float(r["budget"]))
        tol = max(24.0, 0.1 * ref["median_delay_hours"])
        rows.append(
            {
                "path": int(r["path"]),
                "onset_fraction": float(r["onset_fraction"]),
                "budget": float(r["budget"]),
                "q_fixed": q,
                "stratum": "q_lt_1" if q < 1.0 else "q_eq_1_structural",
                "match_exact_events": bool(r["median_delay_events"] == ref["median_delay_events"]),
                "match_tolerance_hours": bool(
                    abs(r["median_delay_hours"] - ref["median_delay_hours"]) <= tol
                ),
            }
        )
    cells = pd.DataFrame(rows, columns=columns)
    strata = {}
    for name, part in cells.groupby("stratum"):
        strata[str(name)] = {
            "n_cells": len(part),
            "n_authorities": len({k // 2 for k in part["path"]}),
            "match_exact_events": float(part["match_exact_events"].mean()),
            "match_tolerance_hours": float(part["match_tolerance_hours"].mean()),
        }
    primary = strata.get("q_lt_1")
    if (
        primary is None
        or primary["n_cells"] < MIN_HB4B_CELLS
        or primary["n_authorities"] < MIN_HB4B_AUTHORITIES
    ):
        state = "INCONCLUSIVE"
    elif primary["match_exact_events"] >= HB4B_MATCH_FRACTION:
        state = "SUPPORTED"
    else:
        state = "WITHDRAWN"
    return {"cells": cells, "n_detectable_cells": len(cells), "strata": strata, "state": state}


def region_report(
    null_cells: pd.DataFrame, hb4b_cells: pd.DataFrame, eligible: list[str], region_of: dict
) -> dict:
    """Per-authority rows and regional clusters (regions with < 3 authorities pooled)."""
    ranked = sorted(eligible)

    def authority(k: int) -> str:
        return ranked[int(k) // 2]

    members: dict[str, set] = {}
    for k in sorted(set(null_cells["path"])) if len(null_cells) else []:
        a = authority(k)
        members.setdefault(region_of.get(a, "UNMAPPED"), set()).add(a)

    def cluster(a: str) -> str:
        r = region_of.get(a, "UNMAPPED")
        return r if len(members.get(r, ())) >= 3 else "other"

    per_authority: dict[str, dict] = {}
    for _, r in null_cells.iterrows():
        a = authority(r["path"])
        d = per_authority.setdefault(
            a, {"region": region_of.get(a, "UNMAPPED"), "cells": 0, "insufficient": 0}
        )
        d["cells"] += 1
        d["insufficient"] += int(not r["passes"])
    clusters: dict[str, dict] = {}
    for a, d in per_authority.items():
        c = clusters.setdefault(
            cluster(a),
            {"authorities": [], "cells": 0, "insufficient": 0, "hb4b_q_lt_1": [0, 0]},
        )
        c["authorities"].append(a)
        c["cells"] += d["cells"]
        c["insufficient"] += d["insufficient"]
    for _, r in hb4b_cells[hb4b_cells.stratum == "q_lt_1"].iterrows():
        c = clusters.get(cluster(authority(r["path"])))
        if c is not None:
            c["hb4b_q_lt_1"][0] += int(r["match_exact_events"])
            c["hb4b_q_lt_1"][1] += 1
    uncertain = json.loads(REGION_MAP.read_text(encoding="utf-8")).get("uncertain", [])
    return {
        "region_map_unverified": True,
        "uncertain_entries": sorted(set(uncertain) & set(per_authority)),
        "per_authority": per_authority,
        "clusters": clusters,
    }


# ---------------------------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------------------------
def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def effective_program_files() -> list[str]:
    """Every repository source file loaded by this runner, plus protocol, data and config files."""
    files: set[str] = set()
    for module in list(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if not name or not str(name).endswith(".py"):
            continue
        try:
            rel = Path(name).resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if rel.split("/")[0] in {"src", "scripts"}:
            files.add(rel)
    files.update(
        {
            PROTOCOL_REL,
            "scripts/run_eia_real_data_validity.py",
            "scripts/verify_wp4_freeze.py",
            "docs/eia_real_data_validity_protocol.md",
            "docs/eia_real_data_validity_freeze.json",
            "docs/research_refinement_v1/stage1/e4_eligibility.json",
            "docs/research_refinement_v1/stage1/e4_eligibility_prerun.json",
            "docs/research_refinement_v1/stage1/e4_region_map.json",
            "docs/research_refinement_v1/stage1/e4_exposure_audit.json",
            "configs/seed_registry.yaml",
            "pyproject.toml",
            "uv.lock",
            "tests/test_e4_heldout.py",
        }
    )
    return sorted(f for f in files if (ROOT / f).is_file())


def wp4_freeze_ok() -> bool:
    import verify_wp4_freeze

    return all(check.ok for check in verify_wp4_freeze.verify())


def read_region_map() -> dict:
    return json.loads(REGION_MAP.read_text(encoding="utf-8"))["region_of"]


# ---------------------------------------------------------------------------------------------
# Core run
# ---------------------------------------------------------------------------------------------
def run_authorities(
    authorities: list[str],
    eligible: list[str],
    out_dir: Path,
    reps: dict,
    *,
    reader=read_series,
    builder=build_respondent_streams,
    wp4_check=wp4_freeze_ok,
    region_of: dict | None = None,
) -> dict:
    """Streams, rule R20 and analyses (a)-(c). R20 failures are retained, never replaced."""
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out_dir}")
    if not wp4_check():
        raise RuntimeError("WP4 freeze record does not verify; stop")
    install_e4_coins()
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    series = reader(authorities)
    timings["read_series_s"] = time.perf_counter() - t0

    paths: list[eva.PathData] = []
    r20: dict[str, dict] = {}
    t0 = time.perf_counter()
    for ba in authorities:
        streams = builder(series, ba, torch.device("cpu"))
        rehearsal = next(s for s in streams if s.window == eva.REHEARSAL)
        procure = int(np.asarray(rehearsal.deployed_action).sum())
        ok = procure >= elig.MIN_REHEARSAL_PROCURE_EVENTS
        r20[ba] = {"rehearsal_procure_events": procure, "passes_R20": ok}
        if ok:
            paths.extend(authority_paths(streams, ba, rank_of(ba, eligible)))
    timings["build_streams_s"] = time.perf_counter() - t0

    result: dict = {"r20": r20, "paths": paths, "timings": timings}
    if not paths:
        return result
    m_family = len(paths) * len(eva.registered_cells())
    t0 = time.perf_counter()
    null_df = e4_null_analysis(paths, reps["null"])
    timings["null_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    unmodified = eva.unmodified_analysis(paths, reps["unmodified"])
    timings["unmodified_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    injected = eva.injected_analysis(paths, reps["injected"])
    timings["injected_s"] = time.perf_counter() - t0
    ns = null_summary(null_df, m_family, reps["null"])
    js = injected_summary(injected, paths)
    result.update(
        null_df=null_df,
        unmodified=unmodified,
        injected=injected,
        null_summary=ns,
        injected_summary=js,
        regions=region_report(
            ns["cells"],
            js["cells"],
            eligible,
            read_region_map() if region_of is None else region_of,
        ),
    )
    return result


def write_outputs(result: dict, out_dir: Path, meta: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        **meta,
        "stage_seconds": {k: round(v, 1) for k, v in result["timings"].items()},
        "r20": result["r20"],
        "n_paths": len(result["paths"]),
        "code_sha256": {f: freeze.file_sha256(ROOT / f) for f in effective_program_files()},
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
        },
        "device": "cpu",
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
            k: ns[k]
            for k in (
                "m_family",
                "level",
                "min_zero_alarm_replicates",
                "n_cells",
                "n_informative_cells",
                "n_insufficient",
                "all_validated",
                "arm_states",
            )
        }
        summary["hb4b"] = {
            "state": js["state"],
            "n_detectable_cells": js["n_detectable_cells"],
            "strata": js["strata"],
        }
        summary["regions"] = result["regions"]
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return summary


def smoke(authority: str, reps: dict) -> None:
    record = elig.load_eligibility()
    dev, locked_ids = record["split"]["development"], record["split"]["locked"]
    if authority in locked_ids:
        raise SystemExit(f"{authority} is a LOCKED authority; the smoke run never opens it")
    if authority not in dev:
        raise SystemExit(f"{authority} is not in the development list")
    out_dir = OUT_ROOT / f"smoke_{authority}"
    started = datetime.now(UTC).isoformat()
    t0 = time.perf_counter()
    result = run_authorities([authority], record["eligible"], out_dir, reps)
    meta = {
        "mode": "smoke",
        "authority": authority,
        "split": "development",
        "replicates": reps,
        "started_utc": started,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "git_head": _git("rev-parse", "HEAD"),
        "command": " ".join(sys.argv),
    }
    summary = write_outputs(result, out_dir, meta)
    keys = ("authority", "runtime_seconds", "stage_seconds", "r20", "paths", "null", "hb4b")
    print(json.dumps({k: summary.get(k) for k in keys}, indent=2, default=str))


# ---------------------------------------------------------------------------------------------
# Locked mode: freeze check, then an atomic one-opening marker, then (and only then) any read
# ---------------------------------------------------------------------------------------------
def acquire_opening(locked_dir: Path, payload: dict) -> Path:
    """Create the opening marker exclusively (O_EXCL). Raises FileExistsError if it exists."""
    locked_dir.mkdir(parents=True, exist_ok=True)
    marker = locked_dir / "opened.json"
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    return marker


def run_locked(
    *,
    freeze_path: Path = FREEZE_RECORD,
    out_root: Path = OUT_ROOT,
    repo_root: Path = ROOT,
    reps: dict | None = None,
    eligibility: dict | None = None,
    reader=read_series,
    builder=build_respondent_streams,
    wp4_check=wp4_freeze_ok,
    region_of: dict | None = None,
) -> dict:
    """Open the locked set once. Order: freeze check, exclusive marker, then any locked read."""
    reps = reps or REPLICATES
    record = freeze.require_freeze(freeze_path, repo_root)  # raises before any marker exists
    missing = [f for f in REQUIRED_FROZEN if f not in record["sha256"]]
    if missing:
        raise RuntimeError(f"freeze record does not list required files: {missing}")
    eligibility = eligibility or elig.load_eligibility()
    locked_ids = list(eligibility["split"]["locked"])
    locked_dir = out_root / "locked"
    try:
        marker = acquire_opening(
            locked_dir,
            {
                "opened_utc": datetime.now(UTC).isoformat(),
                "git_head": _git("rev-parse", "HEAD", cwd=repo_root),
                "freeze_record": str(freeze_path),
                "freeze_record_sha256": freeze.file_sha256(freeze_path),
                "n_locked_authorities": len(locked_ids),
                "note": "Created before any locked value was read. If the run fails, this "
                "marker stays; a re-run needs an explicit, recorded decision by the lead.",
            },
        )
    except FileExistsError as exc:
        raise RuntimeError("locked set already opened once; refusing a second opening") from exc
    started = datetime.now(UTC).isoformat()
    t0 = time.perf_counter()
    result = run_authorities(
        locked_ids,
        eligibility["eligible"],
        locked_dir / "results",
        reps,
        reader=reader,
        builder=builder,
        wp4_check=wp4_check,
        region_of=region_of,
    )
    meta = {
        "mode": "locked",
        "split": "locked",
        "replicates": reps,
        "started_utc": started,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "git_head": _git("rev-parse", "HEAD", cwd=repo_root),
        "freeze_record_sha256": freeze.file_sha256(freeze_path),
        "marker": str(marker),
    }
    return write_outputs(result, locked_dir / "results", meta)


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
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sm = sub.add_parser("smoke")
    sm.add_argument("--authority", required=True)
    sm.add_argument("--null-reps", type=int, default=REPLICATES["null"])
    sm.add_argument("--unmodified-reps", type=int, default=REPLICATES["unmodified"])
    sm.add_argument("--injected-reps", type=int, default=REPLICATES["injected"])
    sub.add_parser("exposure-audit")
    sub.add_parser("freeze-list")
    sub.add_parser("locked")
    args = parser.parse_args()
    if args.mode == "smoke":
        reps = {
            "null": args.null_reps,
            "unmodified": args.unmodified_reps,
            "injected": args.injected_reps,
        }
        smoke(args.authority, reps)
    elif args.mode == "exposure-audit":
        print(exposure_audit().relative_to(ROOT).as_posix())
    elif args.mode == "freeze-list":
        print(json.dumps(effective_program_files(), indent=2))
    else:
        summary = run_locked()
        keys = ("runtime_seconds", "r20", "null", "hb4b")
        print(json.dumps({k: summary.get(k) for k in keys}, indent=2, default=str))


if __name__ == "__main__":
    main()
