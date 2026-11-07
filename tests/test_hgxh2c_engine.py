"""Tests for src/shiftlab/hgxh2c engines, tapes and baselines (docs/hgxh2c/PROTOCOL.md)."""

import importlib
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import torch

from shiftlab.hgxh2c import baselines as BL
from shiftlab.hgxh2c import engines as E
from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.evaluate import run as eval_run

ROOT = Path("C:/Users/nigel/OneDrive/桌面/ICML")
H2C = (
    ROOT
    / "branch-research-h2c-strong-baselines-and-generalization-2026-10-30/src/shiftlab/sota_search"
)
GAP = ROOT / "branch-research-shiftlab-mandate-gap-closure-2026-10-30/src/shiftlab/gap"
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def _load(pkg, path):
    """Import a package directory from a sibling worktree under the name shiftlab.<pkg> (tests only)."""
    name = f"shiftlab.{pkg}"
    if name in sys.modules and getattr(sys.modules[name], "__path__", None) == [str(path)]:
        return
    m = types.ModuleType(name)
    m.__path__ = [str(path)]
    sys.modules[name] = m


def raw_tape(S=64, T=500, frac=0.2, d=5, seed=1, shift=1.4):
    """Raw-unit tape (decision cost / Brier of a toy deployed model) for exact-mode comparisons."""
    rng = np.random.default_rng(seed)
    p = rng.uniform(0.02, 0.98, (S, T))
    y = (rng.random((S, T)) < np.clip(p * shift, 0, 1)).astype(float)
    act = (p >= 1 / 6).astype(float)
    loss = act * (1 - y) * 1.0 + (1 - act) * y * 5.0
    brier = (p - y) ** 2
    pc = act * (1 - p) * 1.0 + (1 - act) * p * 5.0
    r0 = {"B": 0.17, "C": 0.35}
    tp = lambda a: torch.tensor(a, dtype=torch.float64)
    tape = {"B": tp(brier), "Bhat": tp(p * (1 - p)), "C": tp(loss), "Chat": tp(pc), "d": torch.full((S, T), d, dtype=torch.long),
                "theta": r0, "pmax": {"B": 0.25, "C": 5 / 6}, "frac": frac, "budget": T, "sd": {"B": 1.0, "C": 1.0}}  # fmt: skip
    return tape, {
        "p": p,
        "y": y,
        "loss": loss,
        "brier": brier,
        "r0": r0,
        "T": T,
        "S": S,
        "frac": frac,
    }


def _sim(raw, det):
    det._SOURCE_CACHE["TESTFAM"] = {"loss": (raw["r0"]["C"], 1.0), "brier": (raw["r0"]["B"], 1.0)}
    return {
        "y": raw["y"],
        "p": raw["p"],
        "loss": raw["loss"],
        "brier": raw["brier"],
        "world": types.SimpleNamespace(family="TESTFAM"),
    }


@pytest.fixture(scope="module")
def det():
    if not H2C.exists():
        pytest.skip("h2c worktree absent")
    _load("sota_search", H2C)
    return importlib.import_module("shiftlab.sota_search.detectors")


@pytest.mark.parametrize("frac", [0.1, 0.2])
def test_anchor_ports_match_originals(det, frac):
    tape, raw = raw_tape(frac=frac)
    sim = _sim(raw, det)
    lseed = 3
    tape["U"] = torch.tensor(np.random.default_rng(lseed).random((raw["S"], raw["T"])))
    kw = {"frac": frac, "delay": 5, "lseed": lseed}
    pairs = {
        "H2c": (
            BL.h2c("legacy"),
            "C",
            det.pp_cost_guided(sim, mode="guided_disc", gamma=0.995, **kw),
        ),
        "C1": (
            BL.kelly("C", 0.995, "legacy"),
            "C",
            det.fix_cost(_sim(raw, det), gamma=0.995, uniform_cap=True, **kw),
        ),
        "C2": (BL.ons("C", "legacy"), "C", det.pp_cost_guided(sim, mode="cost_ons", **kw)),
        "HG": (
            BL.hg("legacy"),
            "B",
            det.fix_brier(_sim(raw, det), gamma=0.99, gate_w=100, uniform_cap=True, **kw),
        ),
        "ONS_B": (BL.ons("B", "legacy"), "B", det.pp_ons(sim, risk="brier", **kw)),
    }
    for name, (mon, ch, ref) in pairs.items():
        got = mon.run(tape, keep_paths=True).logW[ch][0].numpy()
        assert np.abs(got - ref).max() < 1e-9, (name, np.abs(got - ref).max())
        assert np.abs(ref[:, -1]).max() > 0.05  # nontrivial sequence


def test_hg_prefix_matches_gap_engine():
    if not GAP.exists():
        pytest.skip("gap worktree absent")
    _load("gap", GAP)
    G = importlib.import_module("shiftlab.gap.engine")
    S, T, frac = 48, 400, 0.2
    tape, raw = raw_tape(S, T, frac)
    U = np.random.default_rng(10_000).random((T, S))
    tape["U"] = torch.tensor(U.T.copy())
    stream = {"brier": raw["brier"], "loss": raw["loss"], "proxy_brier": raw["p"] * (1 - raw["p"]), "proxy_cost": tape["Chat"].numpy(),
                  "r0": {"brier": raw["r0"]["B"], "cost": raw["r0"]["C"]}, "pmax": {"brier": 0.25, "cost": 5 / 6},
                  "score": raw["p"], "x": np.random.default_rng(0).normal(size=(S, T, 4))}  # fmt: skip
    ref = G.run(stream, G.Cfg(risk="brier", frac=frac, gamma=0.99, gate_w=100), delay=5, qseed=0)[
        "logW"
    ]
    got = BL.hg("prefix").run(tape, keep_paths=True).logW["B"][0].numpy()
    assert np.abs(got - ref).max() < 1e-4
    assert np.abs(ref[:, -1]).max() > 0.05


# --------------------------------------------------------------------------- reference adapter (A1.2)
from shiftlab.hgxh2c import contract as CT


@pytest.mark.parametrize("regime,delay", [("b20", 5), ("full", 0), ("b05", 20)])
def test_batched_matches_per_event_reference(regime, delay):
    cell = TP.ScenarioCell("coshift", 0.16, delay, regime, "good", 1300)
    tape = TP.generate(cell, "audit", 4, "cpu")
    refs = CT.references()
    alarms_seen = 0
    for name, mk in refs.items():
        mon = BL.REGISTRY[name][0]()
        res = mon.run(tape, keep_paths=True)
        for s in range(4):
            al, paths, spent = CT.run_reference(mk, tape, s)
            for tr, p in paths.items():
                key = tr if tr in res.logW else None
                assert key is not None, (name, tr)
                got = (
                    res.logW[tr][0, s].numpy()
                    if tr == "J"
                    else res.logW[{"B": "B", "C": "C"}[tr]][0, s].numpy()
                )
                assert np.abs(got - np.array(p)).max() < 1e-6, (
                    name,
                    s,
                    np.abs(got - np.array(p)).max(),
                )
                assert int(res.alarm[tr][0, s]) == al[tr], (name, s, tr)
                alarms_seen += al[tr] < 1300
            assert spent == int(res.spent[0, s]), name
    assert alarms_seen > 0


# --------------------------------------------------------------------------- validity, semantics, budget
VALID = [n for n, (_, _, fid, notes) in BL.REGISTRY.items()
         if "EMPIRICAL_ALARM" not in notes and "DIFFERENT_NULL" not in notes]  # fmt: skip


@pytest.mark.parametrize("fam", ["null_stationary", "null_boundary"])
def test_null_far(fam):
    cell = TP.ScenarioCell(fam, 0.0, 5, "b20", "good", 400)
    tape = TP.generate(cell, "audit", 2000, "cpu")
    se = (0.05 * 0.95 / 2000) ** 0.5
    for name in VALID:
        res = BL.REGISTRY[name][0]().run(tape)
        tr = BL.REGISTRY[name][1]
        far = float((res.alarm[tr][0] < 400).double().mean())
        assert far <= 0.05 + 3 * se, (name, tr, far)


def _clone(t):
    return {k: (v.clone() if isinstance(v, torch.Tensor) else v) for k, v in t.items()}


def test_stake_never_uses_unreleased_labels():
    d, s0, T = 7, 100, 300
    tape = TP.generate(TP.ScenarioCell("coshift", 0.08, d, "full", "good", T), "audit", 3, "cpu")
    adv = _clone(tape)
    adv["C"][:, s0:] = 1.0  # adversarial: huge losses from s0 on
    adv["B"][:, s0:] = 1.0
    for name in ["C1", "C2", "H2c", "HG", "timans_grid_C", "joint_ctx_ons"]:
        a = BL.REGISTRY[name][0]().run(tape, keep_paths=True)
        b = BL.REGISTRY[name][0]().run(adv, keep_paths=True)
        for tr in a.lam:
            assert torch.equal(a.lam[tr][..., : s0 + d + 1], b.lam[tr][..., : s0 + d + 1]), (
                name,
                tr,
            )
        assert any(
            not torch.equal(a.lam[tr][..., s0 + d + 1], b.lam[tr][..., s0 + d + 1]) for tr in a.lam
        ), name
        for tr in a.logW:
            assert torch.equal(a.logW[tr][..., : s0 + d], b.logW[tr][..., : s0 + d]), (name, tr)
    # nothing queried: unlabelled outcomes can change nothing at all
    nq = _clone(tape)
    nq["U"] = torch.ones_like(nq["U"])
    nq["frac"] = 0.2
    nq2 = _clone(nq)
    nq2["B"], nq2["C"] = torch.rand_like(nq["B"]), torch.rand_like(nq["C"])
    r1 = BL.REGISTRY["H2c"][0]().run(nq, keep_paths=True)
    r2 = BL.REGISTRY["H2c"][0]().run(nq2, keep_paths=True)
    assert torch.equal(r1.logW["C"], r2.logW["C"])
    assert int(r1.spent.max()) == 0


@pytest.mark.parametrize("boost", [False, True])
def test_budget_never_exceeded(boost):
    tape = TP.generate(TP.ScenarioCell("coshift", 0.08, 5, "b20", "good", 400), "audit", 64, "cpu")
    tape["frac"], tape["budget"] = 0.5, 37
    hooks = E.Hooks(query=lambda ctx, q: torch.ones_like(q)) if boost else E.Hooks()
    res = E.Monitor([E.TrackSpec("C", gamma=0.99)], hooks=hooks).run(tape, keep_paths=True)
    assert int(res.spent.max()) == 37 and int(res.spent.min()) == 37
    assert (res.cumq.diff(dim=-1) >= 0).all()


def test_csillag_full_label_limit_and_repo_factor():
    from shiftlab.dive.prediction_powered_evalues import PredictionPoweredEProcess

    tape = TP.generate(TP.ScenarioCell("coshift", 0.16, 5, "full", "noisy", 500), "audit", 8, "cpu")
    a = E.Monitor([E.TrackSpec("C", corr="csillag", gamma=0.995)]).run(tape, keep_paths=True)
    b = E.Monitor([E.TrackSpec("C", gamma=0.995)]).run(tape, keep_paths=True)
    assert (a.logW["C"] - b.logW["C"]).abs().max() < 1e-12
    # independent factor check at q = 1/2 against the repo's Csillag factor (fixed stake, d = 0)
    t2 = TP.generate(TP.ScenarioCell("coshift", 0.16, 0, "b20", "good", 300), "audit", 4, "cpu")
    t2["frac"], t2["budget"] = 0.5, 300
    res = E.Monitor([E.TrackSpec("C", base="fixed", lam=0.3)]).run(t2, keep_paths=True)
    th, pm = t2["theta"]["C"], t2["pmax"]["C"]
    lam = 0.3 * 0.5 / (pm * (1 / 0.5 - 1) + th)
    for s in range(4):
        ppe = PredictionPoweredEProcess(lower=1 - lam * th, upper=1 + lam * (1 - th))
        q = (t2["U"][s] < 0.5).tolist()
        for t in range(300):
            h, r = float(t2["Chat"][s, t]), float(t2["C"][s, t])
            ppe.update(proxy_factor=1 + lam * (h - th), queried=q[t], propensity=0.5,
                       observed_factor=1 + lam * (r - th) if q[t] else None)  # fmt: skip
        assert abs(ppe.log_wealth - float(res.logW["C"][0, s, -1])) < 1e-9


def test_determinism_and_disjoint_partitions():
    cell = TP.ScenarioCell("lagged", 0.08, 5, "b05", "biased", 300)
    a, b = TP.generate(cell, "dev", 16), TP.generate(cell, "dev", 16)
    assert all(torch.equal(a[k], b[k]) for k in ("B", "C", "Bhat", "Chat", "U"))
    half = TP.generate(cell, "dev", 8)
    assert torch.equal(half["B"], a["B"][:8])
    c = TP.generate(cell, "audit", 16)
    assert not torch.equal(a["B"], c["B"]) and not torch.equal(a["U"], c["U"])
    seeds = {
        p: {TP.seed_of(base, "k", i) for i in range(20000)} for p, base in TP.PARTITIONS.items()
    }
    ps = list(seeds)
    assert all(not (seeds[x] & seeds[y]) for i, x in enumerate(ps) for y in ps[i + 1 :])
    # a monitor never sees the evaluator dict: results are identical when it is removed
    m1 = BL.REGISTRY["H2c"][0]().run(a).alarm["C"]
    a2 = {k: v for k, v in a.items() if k != "eval"}
    assert torch.equal(m1, BL.REGISTRY["H2c"][0]().run(a2).alarm["C"])


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no cuda")
def test_gpu_cpu_agree():
    cell = TP.ScenarioCell("coshift", 0.16, 5, "b20", "good", 400)
    tc, tg = TP.generate(cell, "audit", 32, "cpu"), TP.generate(cell, "audit", 32, "cuda")
    for name in [
        "HG",
        "H2c",
        "C2",
        "joint_ctx_ons",
        "timans_grid_C",
        "timans_approx_C",
        "xu_C",
        "pprm_B",
        "csillag_C",
        "tenzer_ppi_C",
    ]:
        a = BL.REGISTRY[name][0]().run(tc, keep_paths=True)
        b = BL.REGISTRY[name][0]().run(tg, keep_paths=True)
        for tr in a.logW:
            assert (a.logW[tr].cpu() - b.logW[tr].cpu()).abs().max() < 1e-5, (name, tr)
        for tr in a.alarm:
            assert torch.equal(a.alarm[tr].cpu(), b.alarm[tr].cpu()), (name, tr)
    for name in ["ryu_wornell", "cusum_C", "ph_B"]:
        a, b = BL.REGISTRY[name][0]().run(tc), BL.REGISTRY[name][0]().run(tg)
        for tr in a.alarm:
            assert torch.equal(a.alarm[tr].cpu(), b.alarm[tr].cpu()), name


def test_evaluate_columns_smoke():
    df = eval_run(
        list(BL.REGISTRY), TP.ScenarioCell("coshift", 0.16, 5, "b20", "good", 300), "dev", 8, "cpu"
    )
    from shiftlab.hgxh2c.stats import COLUMNS

    assert set(COLUMNS) <= set(df.columns)
    for c in ["loss_before_alarm", "cumulative_decision_cost", "n_interventions", "n_switches", "intervention_cost",
              "switching_cost", "info_cost", "mean_logW_B", "peak_mem_mb"]:  # fmt: skip
        assert c in df.columns
    assert df.method_id.nunique() == len(BL.REGISTRY) and df.J_cost.notna().all()


# --------------------------------------------------------------------------- vectorised fast path == event loop
@pytest.mark.parametrize("cell", [("coshift", 0.16, 5, "b20", "good"), ("opposed", 0.08, 0, "full", "biased"),
                                  ("cost_only", 0.16, 20, "b05", "noisy")])  # fmt: skip
def test_fast_path_equals_loop(cell):
    tp = TP.generate(TP.ScenarioCell(*cell, 500), "audit", 16, "cpu")
    n_fast = 0
    for name, (ctor, _, _, _) in BL.REGISTRY.items():
        m = ctor()
        if not isinstance(m, E.Monitor) or not m._fast_ok():
            continue
        n_fast += 1
        a = m.run(tp, keep_paths=True)
        m.fast = False
        b = m.run(tp, keep_paths=True)
        for k in a.logW:
            assert (a.logW[k] - b.logW[k]).abs().max() < 1e-9, (name, k)
        for k in a.alarm:
            assert torch.equal(a.alarm[k], b.alarm[k]) and torch.equal(a.nq_at[k], b.nq_at[k]), (
                name,
                k,
            )
            assert (a.lw_mean[k] - b.lw_mean[k]).abs().max() < 1e-9, (name, k)
        assert torch.equal(a.cumq, b.cumq) and torch.equal(a.spent, b.spent), name
        assert all((a.lam[k] - b.lam[k]).abs().max() < 1e-9 for k in b.lam), name
    assert n_fast >= 25


def test_hooked_monitor_uses_loop_and_scales_in_k():
    """A non-static hook forces the general loop; K candidates share one wide batch."""
    tp = TP.generate(TP.ScenarioCell("coshift", 0.16, 5, "b20", "good", 300), "audit", 8, "cpu")
    hk = E.Hooks(query=lambda ctx, q: q * (1.0 + (ctx.logW["C"] > 0.5).double()))
    gam = [0.95, 0.99, 0.999]
    wide = E.Monitor([E.TrackSpec("C", gamma=gam)], hooks=hk)
    assert not wide._fast_ok() and wide.K == 3
    rw = wide.run(tp, keep_paths=True)
    for i, g in enumerate(gam):
        r1 = E.Monitor([E.TrackSpec("C", gamma=g)], hooks=hk).run(tp, keep_paths=True)
        assert (rw.logW["C"][i] - r1.logW["C"][0]).abs().max() < 1e-12


def test_classic_closed_form_matches_scalar_recursion():
    cell = TP.ScenarioCell("coshift", 0.16, 5, "b20", "good", 400)
    tp = TP.generate(cell, "audit", 3, "cpu")
    for kind, c in [("cusum", 0.25), ("ph", 0.05)]:
        mon = E.ClassicMonitor(kind, "C")
        _, path, _ = mon.stat_max(tp)
        th, sd = tp["theta"]["C"], tp["sd"]["C"]
        for s in range(3):
            q, B = tp["frac"], tp["budget"]
            spent, buckets, stat, m, mn = 0, {}, 0.0, 0.0, 0.0
            for t in range(400):
                Q = float(tp["U"][s, t]) < q and spent < B
                spent += Q
                if Q:
                    buckets[t + int(tp["d"][s, t])] = (
                        buckets.get(t + int(tp["d"][s, t]), 0.0)
                        + (float(tp["C"][s, t]) - th) / sd
                        - c
                    )
                v = buckets.pop(t, None)
                if kind == "cusum":
                    stat = max(0.0, stat + v) if v is not None else stat
                    cur = stat
                else:
                    m += v or 0.0
                    mn = min(mn, m)
                    cur = m - mn
                assert abs(cur - float(path[s, t])) < 1e-4, (kind, s, t)
