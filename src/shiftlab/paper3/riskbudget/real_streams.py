"""F3 real-stream check (protocol: 2026_programme/05F_F3_REAL_STREAM_PROTOCOL.md).

Registry of the cached paired 0/1 loss streams (14, as pre-registered; two lack recorded provenance, see NO_PROVENANCE), the three feedback conditions, the arm list
(frozen specs, budget restated as R = 2k + h) and the per-episode runner. New code only.
"""

from __future__ import annotations

import copy
import json
import zlib
from pathlib import Path

import numpy as np

from ..contracts import Costs, ProblemSpec
from ..simulation import CONFIG_DIR, Tape, run_policy
from .harness import ROOT
from .harness_v2 import DIAG, make_arm_v2
from .metrics import harm_summary

ARMS_FILE = CONFIG_DIR / "f3_confirmation_arms_v1.json"
T, B, C_Q, K = 2000, 200, 0.05, 5.0
HS = (6, 14, 24, 50, 100)
CONDITIONS = ("clean", "dropout_adverse", "delay_adverse")
P_DROP, EXTRA_DELAY = 0.6, 400
ATLAS_DIR = ROOT / "data" / "atlas_v2_losses"
SPRINT_DIR = ROOT / "data" / "sprint_fresh_losses"

# stream -> (directory, label delay); atlas delays = REAL_DELAYS of run_atlas_v2.py
_ALL14: dict[str, tuple[Path, int]] = {
    "airlines": (ATLAS_DIR, 100),
    "bank": (ATLAS_DIR, 100),
    "criteo": (ATLAS_DIR, 100),
    "elec2": (ATLAS_DIR, 48),
    "openml_ldpa": (ATLAS_DIR, 100),
    "rialto": (ATLAS_DIR, 100),
    "spam": (ATLAS_DIR, 50),
    "uci_occupancy": (ATLAS_DIR, 100),
    "weather": (ATLAS_DIR, 1),
    "appliances": (SPRINT_DIR, 144),
    "beijing_pm25": (SPRINT_DIR, 24),
    "bike_hour": (SPRINT_DIR, 24),
    "household_power": (SPRINT_DIR, 144),
    "metro": (SPRINT_DIR, 24),
}
# Dropped 2026-11-22: neither stream's source, task nor models is recorded anywhere in the repository.
# Restored 2026-11-25: the pre-registered study (05F) covers all 14 streams; the 12-stream view is a
# sensitivity analysis (results/riskbudget/sensitivity_12streams/). Set NO_PROVENANCE to reproduce it.
NO_PROVENANCE = ("openml_ldpa", "uci_occupancy")
EXCLUDED: tuple[str, ...] = ()
STREAMS: dict[str, tuple[Path, int]] = {k: v for k, v in _ALL14.items() if k not in EXCLUDED}
HARMFUL = ("airlines", "bank")
BENEFICIAL = tuple(s for s in STREAMS if s not in HARMFUL)

ROW_FIELDS = (
    "J",
    "J_never",
    "n_queries",
    "n_switches",
    "sup_harm",
    "final_harm",
    "frac_time_deployed",
    *DIAG,
)


def load_stream(name: str) -> tuple[np.ndarray, np.ndarray]:
    d = np.load(STREAMS[name][0] / f"{name}.npz")
    return d["l0"], d["l1"]


def delay_of(name: str) -> int:
    return STREAMS[name][1]


def corruption_rng(stream: str, episode: int, condition: str) -> np.random.Generator:
    """Deterministic per (stream, episode, condition); independent of policy seeds."""
    key = [zlib.crc32(stream.encode()), int(episode), zlib.crc32(condition.encode()), 5001]
    return np.random.default_rng(key)


def make_real_tape(
    l0_row: np.ndarray, l1_row: np.ndarray, delay: int, condition: str, rng: np.random.Generator
) -> Tape:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition}")
    l0, l1 = np.asarray(l0_row), np.asarray(l1_row)
    n = len(l0)
    unfav = l0 < l1  # challenger wrong, incumbent right
    u = rng.random(n)  # always drawn so the stream of draws does not depend on the condition
    d = np.full(n, int(delay), dtype=int)
    if condition == "dropout_adverse":
        d = np.where(unfav & (u < P_DROP), n + 1, d)
    elif condition == "delay_adverse":
        d = d + EXTRA_DELAY * unfav.astype(int)
    return Tape(
        np.column_stack([l0, l1]).astype(float),
        l0 != l1,
        np.zeros((n, 2)),
        d.astype(int),
        {"condition": condition, "delay_kind": condition},
    )


def make_real_spec(delay: int, condition: str) -> ProblemSpec:
    costs = Costs(c_q=C_Q, k=K, c_compute=0.0, c_retrain=0.0)
    if condition == "clean":
        return ProblemSpec(T=T, B=B, costs=costs, delay_known=int(delay), delay_kind="fixed")
    return ProblemSpec(T=T, B=B, costs=costs, delay_known=None, delay_kind="informative")


# ------------------------------------------------------------------------------------------
# arms
# ------------------------------------------------------------------------------------------
def R_of(h: float) -> float:
    return 2 * K + h


def build_real_arms() -> list[dict]:
    """Frozen specs from the registered JSON; budgets restated as R = 2k + h."""
    src = {a["name"]: a for a in json.loads(ARMS_FILE.read_text())["arms"]}
    arms = [copy.deepcopy(src[n]) for n in ("never", "wald_cut", "cusum", "gate_wald")]
    arms += [copy.deepcopy(src[n]) for n in ("cusum_rb_h4", "cusum_rb_h8")]
    for h in HS:
        for tmpl, tag in (
            ("stoploss_R20", "stoploss"),
            ("f3_pi1_R20", "f3_pi1"),
            ("f3v2d_R20", "f3v2d"),
        ):
            a = copy.deepcopy(src[tmpl])
            a["name"], a["R"] = f"{tag}_h{h}", R_of(h)
            arms.append(a)
        if h == 14:
            a = copy.deepcopy(src["f3v2_R20_blind8"])
            a["name"], a["R"] = "f3v2_blind8_h14", R_of(h)
            arms.append(a)
    return arms


def arm_R(arm: dict) -> float | None:
    return arm.get("R")


def make_real_arm(arm: dict, delay: int):
    """Policy for one arm; the v2 window parameter is the stream's declared delay."""
    a = copy.deepcopy(arm)
    if a["type"] == "f3v2":
        a["shield"]["window"] = int(delay)
    return make_arm_v2(a, T)


def run_arm_row(arm: dict, tape: Tape, spec: ProblemSpec, delay: int, seed: int) -> dict:
    pol = make_real_arm(arm, delay)
    rec = run_policy(pol, tape, spec, seed)
    row = {
        "J": rec.J,
        "J_never": float(tape.ell[:, 0].sum()),
        "n_queries": float(rec.ledger["n_queries"]),
        "n_switches": float(rec.ledger["n_switches"]),
        "frac_time_deployed": float(np.mean(rec.a)),
        **harm_summary(tape, rec, spec.costs.k),
    }
    for k in DIAG:
        if hasattr(pol, k):
            row[k] = float(getattr(pol, k))
    return row
