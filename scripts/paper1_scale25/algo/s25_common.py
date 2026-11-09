# ruff: noqa
"""Shared helpers for the Paper 1 scale-25 workstream B (algorithm / mechanism).

Two development pools, never merged inside a run:
  nine  : the nine registered windows (tr.sealed_paths(), checksum verified), seed bases per batch
  fresh : the 7 eligible fresh 2025-26 windows (sealed arrays live in the foundation worktree),
          seed base 2026111901 (doc 19), checksum verified against fresh_registration.json
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P1 = ROOT / "scripts/paper1_eqsdp"
for _p in (
    HERE,
    P1 / "search60",
    P1,
    ROOT / "scripts/qsg_methods_search",
    ROOT / "scripts/failure_atlas_v2_flq",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import pandas as pd

FOUND = Path("C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-paper1-eqsdp-2026-11-08")
MAIN = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
OUT = ROOT / "outputs/paper1_scale25/algo"
DOCS = ROOT / "docs/paper1_scale25"
T = 2000
CQ, CS = 0.05, 5.0
EQ_CUT, W_CUT, ARM_R = "s2armr_H1100", "s2wald_l0.98_g0.3_H1100", "EQSDp_l0.98_g0.3"
EQ_PAIR, W_PAIR = "P2_K2__E48_F60", "P4W__P2_K2__E48_F60"
WALD_PARENT = {"kind": "wald", "lam": 0.98, "gamma": 0.3, "cutoff": 1100}
NINE_REC = FOUND / "outputs/paper1_eqsdp/search60/full"
FRESH_REC = FOUND / "outputs/paper1_eqsdp/fresh/records_all.jsonl"
PANEL_DIR = MAIN / "outputs/qsg_methods_search/sota_expansion"
SEEDS = tuple(range(10))


def nine_sealed():
    import trace_run as tr

    return tr.sealed_paths()


def fresh_sealed():
    reg = json.loads(
        (ROOT / "docs/paper1_eqsdp/fresh_registration.json").read_text(encoding="utf-8")
    )
    out, sb = {}, reg["seed_base"]
    for d in reg["datasets"]:
        if not d.get("eligibility", {}).get("eligible", d.get("eligible", True)):
            continue
        p = FOUND / d["sealed_path"]
        z = np.load(p)
        h = hashlib.sha256(z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes())
        if h.hexdigest() != d["array_content_sha256"]:
            raise SystemExit(f"checksum mismatch {d['name']}")
        out[d["name"]] = (str(p), int(z["delay"]), sb)
    return out


def sealed(pool):
    return {"nine": nine_sealed, "fresh": fresh_sealed}[pool]()


def losses_of(pool_sealed, ds, ep):
    p = pool_sealed[ds][0]
    z = np.load(p)
    return z["l0"][ep].astype(np.int8), z["l1"][ep].astype(np.int8)


# ---------------------------------------------------------------- records
COLS = [
    "net",
    "loss",
    "labels",
    "switches",
    "late_adoption",
    "false_promotion",
    "reversal_churn",
    "label_spend",
    "residual",
    "regret",
]


def read_jsonl(path, keep=None):
    return pd.read_json(path, lines=True, dtype={"config_id": str})


def load_nine_search60(names=None):
    """Matched full-data records (all episodes, 10 seeds) of search60 batches, by config_id."""
    fr = []
    for d in sorted(NINE_REC.glob("p[34]*")):
        f = d / "records.jsonl"
        if d.name.startswith("p4_cal") or not (d / "DONE").exists() or not f.exists():
            continue
        x = read_jsonl(f)
        if names is not None:
            x = x[x.config_id.isin(names)]
        if len(x):
            fr.append(x)
    return pd.concat(fr).drop_duplicates(["stream", "ep", "seed", "config_id"])


def load_nine_panel():
    fr = []
    for t in ("nine", "nine_armR", "batch2"):
        d = pd.read_json(PANEL_DIR / t / "records.jsonl", lines=True, dtype={"policy": str})
        nine = set(nine_sealed())
        d = d[d.stream.isin(nine)].rename(columns={"policy": "config_id"})
        fr.append(d)
    return pd.concat(fr).drop_duplicates(["stream", "ep", "seed", "config_id"])


def load_fresh():
    return read_jsonl(FRESH_REC).drop_duplicates(["stream", "ep", "seed", "config_id"])


def ep_table(df, cols=("net", "loss", "labels", "switches")):
    """Seed-averaged per (stream, ep, config_id)."""
    c = [k for k in list(cols) + COLS[4:] if k in df.columns]
    return df.groupby(["stream", "ep", "config_id"])[c].mean()


def boot_eq(vals_by_stream, nb=2000, seed=0):
    """Stratified episode bootstrap of the equal-dataset mean of a per-episode quantity."""
    rng = np.random.default_rng(seed)
    acc = 0
    for v in vals_by_stream:
        v = np.asarray(v, float)
        acc = acc + v[rng.integers(0, len(v), size=(nb, len(v)))].mean(1)
    return acc / len(vals_by_stream)


def ci(reps):
    lo, hi = np.quantile(reps, [0.025, 0.975])
    return float(lo), float(hi)
