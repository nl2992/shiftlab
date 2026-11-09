# ruff: noqa
"""Functional / causality tests for the workstream-B modules (CPU-sized).

    python -m pytest scripts/paper1_scale25/algo/test_algo.py -q      (or run this file)
1. all-off identity: an empty-module spec equals the frozen parent bitwise (EQ and Wald).
2. budget: no candidate exceeds B=200 labels; purchases stop after the cutoff (t + delay <= T - 1100).
3. causality / no future-label access: replacing the loss stream from event t0 on leaves the deployed
   path and every request decision before t0 unchanged (labels bought earlier but released after t0 can
   only change decisions at or after their release, which is after t0, so the prefix is unaffected).
"""

import hashlib

import numpy as np
import pytest
import s25_common as sc
import s25_modules  # noqa: F401
import s25_v2  # noqa: F401
import compositor as comp
import trace_run as tr
from suite import build_suite, run_episode, stream_from_losses
import c4_pilot

import v2_specs

EP = [("sf_311", 3, 0), ("kc_311", 37, 1), ("dc_311", 10, 2)]
SPECS = {s["name"]: s for s in v2_specs.specs()}
SPECS["UNI_t"] = {"name": "UNI_t", "modules": [{"id": "UNI", "params": {"n_target": 50}}]}
SPECS["UNC_t"] = {"name": "UNC_t", "modules": [{"id": "UNC", "params": {"c": 0.4}}]}
SPECS["OFF"] = {"name": "OFF", "modules": []}
SPECS["OFFW"] = {"name": "OFFW", "modules": [], "parent": sc.WALD_PARENT}
PICK = [
    "OFF",
    "OFFW",
    "UNI_t",
    "UNC_t",
    "V2A_E48_d0.75_l50_h0.002",
    "V2B_both_k1.0",
    "V2C_EAP_g0.4_m1.0",
    "V2D_DPW_m1.0",
    "V2E_INS_a80",
    "V2F_LSW_z0.5_m1.0",
    "V2G_F59tree",
]


def run_one(name, l0, l1, ds, ep, seed, sealed):
    comp.register_specs([SPECS[name]])
    _, delay, sb = sealed[ds]
    losses = np.stack([l0, l1], axis=1).astype(np.int8)
    cfg = c4_pilot.CFG
    h = int.from_bytes(hashlib.sha256(ds.encode()).digest()[:4], "big")
    T = losses.shape[0]
    (pol,) = build_suite(
        T,
        200,
        cfg["cs"],
        cfg["cq"],
        cfg["alpha"],
        delay,
        ep * 100_000 + seed,
        sb + h % 1000,
        names=[name],
        extra=tr.registry(),
    )
    rng = np.random.default_rng([sb, h, ep, seed, 7])
    preds, labels = stream_from_losses(losses, rng)
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=delay,
        budget=200,
        label_price=cfg["cq"],
        switch_cost=cfg["cs"],
        trace=True,
    )
    dep = np.fromiter((r["deployed_model"] for r in res.records), int, T)
    req = np.fromiter((r["requested"] for r in res.records), int, T)
    return res, dep, req, delay


@pytest.fixture(scope="module")
def sealed():
    return sc.nine_sealed()


def arrays(sealed, ds, ep):
    z = np.load(sealed[ds][0])
    return z["l0"][ep].astype(np.int8), z["l1"][ep].astype(np.int8)


@pytest.mark.parametrize("ds,ep,seed", EP)
def test_all_off_identity(sealed, ds, ep, seed):
    l0, l1 = arrays(sealed, ds, ep)
    for off, ref in (("OFF", sc.EQ_CUT), ("OFFW", sc.W_CUT)):
        SPECS[ref] = None
        comp.register_specs([SPECS[off]])
        a = run_one(off, l0, l1, ds, ep, seed, sealed)[0]
        # reference through the registry (not the compositor)
        _, delay, sb = sealed[ds]
        cfg = c4_pilot.CFG
        h = int.from_bytes(hashlib.sha256(ds.encode()).digest()[:4], "big")
        (pol,) = build_suite(
            2000,
            200,
            cfg["cs"],
            cfg["cq"],
            cfg["alpha"],
            delay,
            ep * 100_000 + seed,
            sb + h % 1000,
            names=[ref],
            extra=tr.registry(),
        )
        preds, labels = stream_from_losses(
            np.stack([l0, l1], 1).astype(np.int8), np.random.default_rng([sb, h, ep, seed, 7])
        )
        b = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=delay,
            budget=200,
            label_price=cfg["cq"],
            switch_cost=cfg["cs"],
            trace=True,
        )
        assert a.net_cost == b.net_cost and a.requested_labels == b.requested_labels


@pytest.mark.parametrize("name", PICK)
@pytest.mark.parametrize("ds,ep,seed", EP)
def test_budget_and_cutoff(sealed, name, ds, ep, seed):
    l0, l1 = arrays(sealed, ds, ep)
    res, dep, req, delay = run_one(name, l0, l1, ds, ep, seed, sealed)
    assert res.requested_labels <= 200
    t = np.flatnonzero(req)
    assert (t + delay <= 2000 - 1100).all()  # cutoff H=1100 respected by every module


@pytest.mark.parametrize("name", PICK)
@pytest.mark.parametrize("ds,ep,seed", EP)
def test_no_future_access(sealed, name, ds, ep, seed):
    l0, l1 = arrays(sealed, ds, ep)
    t0 = 600
    rng = np.random.default_rng(1)
    m0, m1 = l0.copy(), l1.copy()
    m0[t0:] = rng.integers(0, 2, len(m0) - t0)
    m1[t0:] = rng.integers(0, 2, len(m1) - t0)
    _, dep_a, req_a, _ = run_one(name, l0, l1, ds, ep, seed, sealed)
    _, dep_b, req_b, _ = run_one(name, m0, m1, ds, ep, seed, sealed)
    assert (dep_a[:t0] == dep_b[:t0]).all() and (req_a[:t0] == req_b[:t0]).all()
