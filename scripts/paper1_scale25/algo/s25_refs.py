# ruff: noqa
"""Reference-policy tables for the two development pools (reused verified records + new extras)."""

from __future__ import annotations

import json

import pandas as pd
import s25_common as sc
from analyze_all import ADAPTERS, CONTROLS

V1 = [sc.EQ_CUT, sc.W_CUT, sc.EQ_PAIR, sc.W_PAIR]
EXTRA = json.load(open(sc.HERE / "extra_refs.json"))
REF_NAMES = V1 + [sc.ARM_R] + list(ADAPTERS) + list(CONTROLS) + EXTRA


def load_refs(pool, with_new=()):
    """Raw per-seed records for the reference set (+ any extra record dirs given by name)."""
    if pool == "nine":
        a = sc.load_nine_search60(
            [sc.EQ_CUT, sc.EQ_PAIR, sc.W_CUT, sc.W_PAIR, "P1_E48_s0", "P1_F60_s0"]
        )
        b = sc.load_nine_panel()
        b = b[b.config_id.isin(list(ADAPTERS) + list(CONTROLS) + [sc.ARM_R])]
        parts = [a, b]
        new = ["abl_nine", "refgrid_nine"]
    else:
        parts = [sc.load_fresh()]
        new = ["abl_fresh", "refgrid_fresh"]
    for d in list(new) + list(with_new):
        f = sc.OUT / d / "records.jsonl"
        if f.exists() and (sc.OUT / d / "DONE").exists():  # only completed runs
            parts.append(sc.read_jsonl(f))
    x = pd.concat(parts)
    x["config_id"] = (
        x.config_id.str.replace(r"__(?!E48|F60).*$", "", regex=True) if False else x.config_id
    )
    return x.drop_duplicates(["stream", "ep", "seed", "config_id"])


def ep_level(x, seeds=None):
    if seeds is not None:
        x = x[x.seed.isin(list(seeds))]
    return sc.ep_table(x)


def J(x):  # pp of T
    return x.net / sc.T * 100
