"""Policy registry for the SOTA sprint: published ports, earlier ShiftLab candidates, family modules.

Every factory has the Atlas v2 signature ``f(T, B, cs, cq, alpha, delay, r) -> Policy`` where
``r(name)`` returns a private generator. Family modules ``fam_a`` .. ``fam_d`` (one per agent)
each expose ``EXTRA``; a family module that fails to import is reported, not silently dropped.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bench  # noqa: F401  (pins the FLQ regimes module before the RMM path is added)
from v2_extra import EXTRA as _FLQ

IMPORT_ERRORS: dict[str, str] = {}


def _rmm() -> dict:
    """Load the RMM/LRMD line under a private module name (its directory reuses FLQ file names)."""
    path = ROOT / "scripts/failure_atlas_v2/restart_monitor.py"
    spec = importlib.util.spec_from_file_location("atlas_v2_restart_monitor", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    saved = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:  # RMM prepends its own directory, whose regimes.py/suite.py would shadow FLQ's
        sys.path[:] = saved  # (spawned workers inherit the parent's sys.path)
    keep = (
        "gated_deployment+RMM",
        "discern_style+RMM",
        "SMCS+retain-incumbent+RMM",
        "model_picker_adapter+RMM",
        "cams_adapter+RMM",
        "LRMD",
        # Amendment 3 attribution: single-start (no restart mixture) and no continued acquisition
        "gated_deployment+RMM_single",
        "discern_style+RMM_single",
        "SMCS+retain-incumbent+RMM_single",
        "gated_deployment+RMM_noacq",
        "discern_style+RMM_noacq",
    )
    out = {f"rmm:{k}": v for k, v in mod.FACTORIES.items() if k in keep}
    # Amendment 5: a fourth certificate family as RMM host (the strong gated re-port, wmax_t = 1/q_t)
    from strong_hosts import GatedAdaptiveRange

    out["rmm:gated_adaptive_range+RMM"] = lambda T, B, cs, cq, a, d, r: mod.RestartMixtureMonitor(
        lambda T_, B_, a_, r_: GatedAdaptiveRange(T_, B_, a_, rng=r_),
        T,
        B,
        a,
        rng=r("gated_adaptive_range"),
        name="",
    )
    return out


def build_extra() -> dict:
    extra = dict(_FLQ)
    try:
        extra.update(_rmm())
    except (ImportError, AttributeError) as e:  # pragma: no cover - reported in manifests
        IMPORT_ERRORS["rmm"] = repr(e)
    for fam in (
        "fam_a",
        "fam_b",
        "fam_c",
        "fam_d",
        "fam_x",
        "fam_m",
        "fam_h",
        "fam_r",
        "fam_t",
        "fam_p",
        "fam_e",
        "fam_f",
    ):  # sprint 2
        if not (HERE / f"{fam}.py").exists():
            continue
        try:
            extra.update(importlib.import_module(fam).EXTRA)
        except (ImportError, AttributeError) as e:
            IMPORT_ERRORS[fam] = repr(e)
    try:
        extra.update(importlib.import_module("pfa_srr_baseline").EXTRA)
    except (ImportError, AttributeError) as e:
        IMPORT_ERRORS["pfa_srr_baseline"] = repr(e)
    return extra


EXTRA = build_extra()
