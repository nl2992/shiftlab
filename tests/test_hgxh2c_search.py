"""Tests for the typed grammar, stage-3 search machinery and the stage-4 guard (docs/hgxh2c/PROTOCOL.md)."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

from shiftlab.hgxh2c import baselines as BL
from shiftlab.hgxh2c import freeze
from shiftlab.hgxh2c import grammar as G
from shiftlab.hgxh2c import search as SR
from shiftlab.hgxh2c import tapes as TP

ROOT = Path(__file__).resolve().parents[1]
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def cand(slots=None, **kw):
    s = [()] * 6
    for i, v in (slots or {}).items():
        s[i] = v
    return G.Candidate(tuple(s), **kw)


def small_tape(fam="coshift", T=300, n=8, d=5, reg="b20", dev="cpu"):
    return TP.cat_tapes([TP.generate(TP.ScenarioCell(fam, 0.16, d, reg, "good", T), "dev", n, dev)])


def script(name):
    sp = importlib.util.spec_from_file_location(name, ROOT / f"scripts/hgxh2c/{name}.py")
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def test_structures_and_space():
    assert len(G.STRUCTURES) == 64 == 2 ** len(G.SLOTS)
    sz = G.space_size()
    assert sz["structures"] == 64 and sz["canonical"] > 1e6 and sz["raw"] > sz["canonical"]
    cs = list(G.enumerate(300))
    assert len(cs) == len({c.hash for c in cs}) == 300
    assert {c.structure for c in cs} == set(
        range(1, 64)
    )  # all 63 non-empty structures are stratified in
    assert all(G.canonicalise(c)[0] is c for c in cs)


def test_hash_stability():
    a = cand({0: (("ratio", (1.0, 0)),)})
    b = cand({0: (("ratio", (1.0, 0)),)})
    assert (
        a.hash == b.hash
        and a == b
        and G.Candidate.from_dict(json.loads(json.dumps(a.to_dict()))).hash == a.hash
    )
    assert a.hash != cand({0: (("ratio", (0.5, 0)),)}).hash
    assert a.hash == cand({0: (("ratio", (1.0, 0)),)}, comb="bonf", base=("kelly", "kelly")).hash
    assert list(G.enumerate(20)) == list(G.enumerate(20))  # deterministic walk


def test_canonicalise_rejections():
    why = lambda c: G.canonicalise(c)[1]
    assert why(cand()) == "EQUIVALENT_TO:no_transfer"
    assert why(cand({3: (("shift", (0.0,)),)})) == "EQUIVALENT_TO:identity"
    assert why(cand({0: (("ratio", (1.0, 1)),)})) == "EQUIVALENT_TO:discounted_kelly"
    assert (
        why(cand({5: (("gamma", (0.9,)),)}, base=("ons", "kelly"))) == "EQUIVALENT_TO:identity"
    )  # target B is ONS
    assert why(cand({5: (("gamma", (0.9,)),)}, base=("kelly", "ons"))) is None
    assert why(cand({0: (("ratio", (1.0, 0)),)})) is None
    # raw sampling logs rejections with reason codes
    rs = [G.canonicalise(c)[1] for c in G.sample_raw(300)]
    assert any(r and r.startswith("EQUIVALENT_TO:") for r in rs)


def test_typing_rejection(monkeypatch):
    why = lambda c: G.canonicalise(c)[1]
    assert why(cand({0: (("oracle_tau", (1.0,)),)})).startswith("UNTYPED")
    assert why(cand({0: (("ratio", (1.5, 0)),)})).startswith("UNTYPED")  # stake mix outside [0,1]
    assert why(cand({0: (("ratio", (1.0, 0)),)}, qfl=0.0)).startswith(
        "UNTYPED"
    )  # q floor must be > 0
    assert why(cand({0: (("ratio", (1.0, 0)),)}, comb="mix", w=0.3)).startswith(
        "UNTYPED"
    )  # weights fixed before t
    assert (
        why(cand({0: (("ratio", (1.0, 0)),)}, comb="prod")) == "INVALID:product_cross_term"
    )  # A3.1
    monkeypatch.setitem(
        G.OPS, ("S", "oracle"), G.Op(("a",), ((1.0,),), {"a": (0, 1)}, ("eval.tau",))
    )
    monkeypatch.setitem(G.ORDER, "S", G.ORDER["S"] + ["oracle"])
    assert "non-predictable" in why(cand({0: (("oracle", (1.0,)),)}))


def test_constant_ratio_equals_discounted_kelly():
    tape = small_tape()
    r = G.compile(cand({0: (("ratio", (1.0, 1)),)})).run(tape, keep_paths=True)
    c1 = BL.kelly("C", 0.995).run(tape, keep_paths=True)
    assert (r.logW["C"][0] - c1.logW["C"][0]).abs().max() < 1e-9
    assert abs(float(r.logW["C"][0].abs().max())) > 1e-3


def test_h2c_and_hg_are_single_channel_special_cases():
    tape = small_tape()
    h2c, hg = cand({0: (("ratio", (1.0, 0)),)}), cand({3: (("gate", (0.0,)),)})
    assert h2c.group != hg.group  # different guide features -> different wide batches
    r, r2 = (
        G.compile_batch([h2c]).run(tape, keep_paths=True),
        G.compile_batch([hg]).run(tape, keep_paths=True),
    )
    assert (r.logW["C"][0] - BL.h2c().run(tape, keep_paths=True).logW["C"][0]).abs().max() < 1e-9
    assert (r2.logW["B"][0] - BL.hg().run(tape, keep_paths=True).logW["B"][0]).abs().max() < 1e-9
    both = G.compile(cand({0: (("ratio", (1.0, 0)),), 3: (("gate", (0.0,)),)})).run(
        tape, keep_paths=True
    )
    ind = BL.indep_hg_h2c().run(tape, keep_paths=True)
    assert max((both.logW[t][0] - ind.logW[t][0]).abs().max() for t in "BCJ") < 1e-9


def test_batched_equals_single():
    tape = small_tape()
    cs = [c for c in G.enumerate(400) if c.group[:2] == (("kelly", "kelly"), "bonf")]
    cs = [c for c in cs if c.group == cs[0].group][:6]
    assert len(cs) >= 3
    r = G.compile_batch(cs).run(tape, keep_paths=True)
    for k, c in enumerate(cs):
        s = G.compile(c).run(tape, keep_paths=True)
        assert max((r.logW[t][k] - s.logW[t][0]).abs().max() for t in "BC") < 1e-9


def adversarial_tape(S=16, T=200, dev="cpu"):
    g = torch.Generator().manual_seed(3)
    ext = lambda: (torch.rand(S, T, generator=g) < 0.5).double() * 1.0
    th = TP.calibrate()
    prox = lambda: (torch.rand(S, T, generator=g) < 0.5).double() * TP.PMAX
    return {
        "B": ext(),
        "C": ext(),
        "Bhat": prox(),
        "Chat": prox(),
        "U": torch.rand(S, T, generator=g, dtype=torch.float64),
        "d": torch.zeros(S, T, dtype=torch.long),
        "theta": {"B": th[0], "C": th[1]},
        "sd": {"B": th[2], "C": th[3]},
        "pmax": {"B": TP.PMAX, "C": TP.PMAX},
        "frac": 0.2,
        "budget": T,
    }


def test_factors_nonnegative_on_adversarial_tapes():
    tape = adversarial_tape()
    per = {}
    for c in G.enumerate(630):
        per.setdefault(c.structure, c)
    cs = list(per.values())
    assert len(cs) == 63
    groups = {}
    for c in cs:
        groups.setdefault(c.group, []).append(c)
    for grp in groups.values():
        r = G.compile_batch(grp).run(tape, keep_paths=True)
        for t in "BC":
            lw = r.logW[t]
            dl = torch.diff(lw, dim=2, prepend=torch.zeros_like(lw[:, :, :1]))
            assert torch.isfinite(lw).all() and dl.min() >= np.log(0.5) - 1e-9, (t, float(dl.min()))


def test_null_far_sanity_random_candidates():
    tape = small_tape("null_stationary", T=400, n=96, d=5, dev=DEV)
    cs = list(G.enumerate(20, seed=5))
    al = torch.zeros(20, 96, dtype=torch.float64)

    def fn(res, sub):
        al[sub] = (res.alarm["J"] < 400).double().cpu()

    SR.run_cands(cs, tape, fn)
    k = int(al.sum())
    assert SR.cp_lower([k], [20 * 96])[0] <= SR.ALPHA, k


def test_per_seed_matches_evaluate_score():
    from shiftlab.hgxh2c.evaluate import score

    tape = small_tape(T=300, dev=DEV)
    cs = list(G.enumerate(6))
    out = {}

    def fn(res, sub):
        J = SR.per_seed(res, tape)[0]
        for k, i in enumerate(sub):
            ref = score(res, tape, "J", k, "x").J_cost.to_numpy()
            assert np.abs(J[k].cpu().numpy() - ref).max() < 1e-9
            out[i] = 1

    SR.run_cands(cs, tape, fn)
    assert len(out) == 6


def test_registry_append_only(tmp_path):
    import pandas as pd

    reg = SR.Registry(tmp_path / "registry.parquet")
    df = pd.DataFrame({"rung": [0, 0], "hash": ["a", "b"], "status": "evaluated", "dJ": [1.0, 2.0]})
    assert reg.append("r0-c0", df.copy())
    f = tmp_path / "registry.parquet" / "part-r0-c0.parquet"
    before = f.read_bytes()
    assert not reg.append("r0-c0", df.assign(dJ=[9.0, 9.0]))  # existing part is never rewritten
    assert f.read_bytes() == before
    reg.append("r1-c0", df.assign(rung=1))
    r = reg.read()
    assert len(r) == 4 and set(r.rung) == {0, 1}
    assert (
        len(pd.read_parquet(tmp_path / "registry.parquet")) == 4
    )  # readable as one dataset (make_report)


def test_stage4_refuses_without_freeze(tmp_path, monkeypatch):
    ff = tmp_path / "FREEZE.json"
    with pytest.raises(RuntimeError):
        freeze.confirm_seeds_allowed(ff)
    s4 = script("stage4_confirm")
    monkeypatch.setattr(sys, "argv", ["x", "--freeze-file", str(ff), "--out", str(tmp_path / "o")])
    with pytest.raises(RuntimeError):
        s4.main()
    assert not (tmp_path / "o" / "shards").exists()


def test_stage3_smoke_then_stage4_smoke(tmp_path, monkeypatch):
    s3, s4 = script("stage3_search"), script("stage4_confirm")
    ff, o3, o4 = tmp_path / "FREEZE.json", tmp_path / "s3", tmp_path / "s4"
    monkeypatch.setattr(
        sys, "argv", ["x", "--smoke", "--out", str(o3), "--freeze-file", str(ff), "--device", DEV]
    )
    s3.main()
    fin = json.loads((o3 / "finalists.json").read_text())
    assert {"frontier", "finalists", "selector"} <= set(
        freeze.require_frozen(["frontier", "finalists", "selector"], ff)
    )
    assert fin["N_per_cell_alt"] >= 1000 and fin["N_per_cell_null"] >= 1000
    reg = SR.Registry(o3 / "registry.parquet").read()
    assert (
        {0, 1, 2, 3} <= set(reg.rung)
        and "gen_quota" in set(reg.status)
        and "rejected" in set(reg.status)
        and "evaluated" in set(reg.status)
    )
    n_before = len(reg)
    s3.main()  # resume: idempotent, nothing re-evaluated and no rewrite
    assert len(SR.Registry(o3 / "registry.parquet").read()) == n_before
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--smoke",
            "--out",
            str(o4),
            "--freeze-file",
            str(ff),
            "--device",
            DEV,
            "--n",
            "12",
            "--boot",
            "100",
        ],
    )
    s4.main()
    conf = json.loads((o4 / "confirmation.json").read_text())
    assert conf["config"]["partition"] == "confirm"
    for v in conf["finalists"].values():
        assert {
            "vs_baseline",
            "holm_p",
            "iut_pass",
            "ablations",
            "negative_control",
            "power_diff",
            "regime_wins",
            "outcome",
        } <= set(v)
    rep = script("make_report")
    for v in conf["finalists"].values():
        assert isinstance(rep.decide(v), str)


def null_far(mon, tape):
    return float((mon.run(tape).alarm["J"] < tape["B"].shape[1]).double().mean())


def test_linear_combiner_valid_product_inflated():
    """A3.1: correlated B/C, full labels, null_stationary: linear <= alpha + 3 SE; the old product reproduces the inflation."""
    from shiftlab.hgxh2c.engines import Monitor, TrackSpec

    n = 2000
    tape = TP.cat_tapes(
        [
            TP.generate(
                TP.ScenarioCell("null_stationary", 0.0, 0, "full", "good", 2000), "dev", n, DEV
            )
        ]
    )
    tracks = lambda: [TrackSpec("B", gamma=0.99), TrackSpec("C", gamma=0.995)]
    far_prod = null_far(Monitor(tracks(), combiner="prod", fast=False), tape)
    far_lin = null_far(G.compile(cand(comb="linear", w=0.5)), tape)
    far_bonf = null_far(Monitor(tracks(), combiner="bonf"), tape)
    bound = 0.05 + 3 * (0.05 * 0.95 / n) ** 0.5
    assert far_lin <= bound and far_bonf <= bound, (far_lin, far_bonf)
    assert far_prod > bound, far_prod  # THEORY_AUDIT F1: about 0.09


def test_read_sets_per_channel(monkeypatch):
    """A3.2: S and R operators may not read the current proxy (or its residual statistics); Q operators may."""
    assert G.canonicalise(cand({1: (("ipw", (0.5,)),)}))[0] is not None  # Q reads h, res
    for ch, name in (("S", "peek"), ("R", "peekr")):
        monkeypatch.setitem(G.OPS, (ch, name), G.Op(("a",), ((1.0,),), {"a": (0, 1)}, ("h",)))
        monkeypatch.setitem(G.ORDER, ch, G.ORDER[ch] + [name])
        slot = {"S": 0, "R": 2}[ch]
        assert "non-predictable" in G.canonicalise(cand({slot: ((name, (1.0,)),)}))[1]
    monkeypatch.undo()
    assert all(set(o.reads) <= G.READS[ch] for (ch, _), o in G.OPS.items())


def test_grapa_clamped_after_hooks():
    """A3.3: a hook that asks for an absurd stake cannot push a GRAPA base above 0.95/Bd (both engine paths)."""
    from shiftlab.hgxh2c.engines import Hooks, Monitor, TrackSpec

    tape = small_tape(T=250)
    q = float(tape["frac"][0])
    bd = TP.PMAX * (1 / q - 1) + TP.calibrate()[1]
    for fast in (True, False):
        mon = Monitor(
            [TrackSpec("C", base="grapa")],
            hooks=Hooks(stake={"C": lambda ctx, lam: lam * 0 + 1e6}),
            fast=fast,
        )
        lam = mon.run(tape, keep_paths=True).lam["C"]
        assert float(lam.max()) <= 0.95 / bd + 1e-12 and float(lam.max()) > 0.9 / bd


def first_cross(lw, k):
    hit = (lw >= k).nonzero()
    return int(hit[0]) if len(hit) else None


def test_soft_restart_engine_semantics():
    from shiftlab.hgxh2c.engines import Hooks, Monitor, TrackSpec

    tape = small_tape(T=300)
    mk = lambda f: Monitor(
        [TrackSpec("C", gamma=0.995)], hooks=Hooks(restart={"C": f} if f else {}), fast=False
    )
    base = mk(None).run(tape, keep_paths=True).logW["C"]
    at = lambda v: (
        lambda ctx: torch.where(
            ctx.tt == 100, torch.full_like(ctx.logW["C"], v), torch.ones_like(ctx.logW["C"])
        )
    )
    hard = mk(lambda ctx: (ctx.tt == 100).expand_as(ctx.logW["C"]))
    r_hard = hard.run(tape, keep_paths=True).logW["C"]
    r_one = mk(at(1.0)).run(tape, keep_paths=True).logW["C"]
    r_zero = mk(at(0.0)).run(tape, keep_paths=True).logW["C"]
    r_half = mk(at(0.5)).run(tape, keep_paths=True).logW["C"]
    assert (r_one - base).abs().max() < 1e-12  # keep = 1 is the identity
    assert (r_zero - r_hard).abs().max() < 1e-12  # float keep = 0 equals the boolean hard reset
    assert (
        r_half[:, :, :101] - base[:, :, :101]
    ).abs().max() < 1e-12  # nothing changes before the restart
    assert (r_half - base).abs().max() > 1e-6 and (
        r_half - r_zero
    ).abs().max() > 1e-6  # soft differs from both


def test_soft_restart_operator_fires_on_source_upcrossing():
    tape = small_tape("coshift", T=400, n=8, d=0, reg="full")
    ref = cand({0: (("shift", (0.1,)),)})
    both = cand({0: (("shift", (0.1,)),), 2: (("soft", (0.3,)),)})
    rs = G.compile(ref).run(tape, keep_paths=True)
    rb = G.compile(both).run(tape, keep_paths=True)
    src = rs.logW["B"][0]  # source (B) wealth is unaffected by BC operators
    assert (rb.logW["B"][0] - src).abs().max() < 1e-12
    diff = (rb.logW["C"][0] - rs.logW["C"][0]).abs()
    fired = [s for s in range(src.shape[0]) if first_cross(src[s], 0.5) is not None]
    for s in fired:
        assert (
            diff[s, : first_cross(src[s], 0.5) + 1].max() < 1e-12
        )  # identical until the source up-crosses 0.5
    assert any(
        diff[s].max() > 1e-9 for s in fired
    )  # and different afterwards (the state was scaled by rho)


def test_gamma_switch_operator():
    tape = small_tape("coshift", T=400, n=8, d=0, reg="full")
    ref = cand({0: (("shift", (0.1,)),)})
    sw = cand({0: (("shift", (0.1,)),), 2: (("gamma", (0.9,)),)})
    rr = G.compile(ref).run(tape, keep_paths=True)
    rw = G.compile(sw).run(tape, keep_paths=True)
    src = rr.logW["B"][0]
    diff = (rw.logW["C"][0] - rr.logW["C"][0]).abs()
    fired = [s for s in range(src.shape[0]) if first_cross(src[s], 1.0) is not None]
    assert fired
    for s in fired:
        assert (
            diff[s, : first_cross(src[s], 1.0) + 1].max() < 1e-12
        )  # discount unchanged before the switch
    assert max(float(diff[s].max()) for s in fired) > 1e-9  # different afterwards
    on = cand(
        {2: (("gamma", (0.9,)),)}, base=("kelly", "ons")
    )  # ONS ignores the discounted moments: numerically the identity
    assert G.canonicalise(on)[1] == "EQUIVALENT_TO:identity"
    a = G.compile(on).run(tape, keep_paths=True).logW["C"]
    b = G.compile(cand({}, base=("kelly", "ons"))).run(tape, keep_paths=True).logW["C"]
    assert (a - b).abs().max() < 1e-12


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA graphs need a GPU")
def test_graph_equals_eager_for_every_operator():
    full = {
        0: (("ratio", (1.0, 0)), ("temper", (0.25,))),
        1: (("straddle", (2.0, 0.0)), ("pace", (1.0, 2.0))),
        2: (("restart", (1.0,)), ("soft", (0.3,))),
        3: (("shift", (0.3,)), ("gate", (0.0,))),
        4: (("boost", (3.0,)), ("ipw", (1.0,))),
        5: (("soft", (0.6,)), ("gamma", (0.9,))),
    }
    tape = small_tape(T=250, n=8, dev="cuda")
    for base, comb in ((("kelly", "kelly"), "bonf"), (("grapa", "kelly"), "linear")):
        c = cand(full, comb=comb, w=0.5 if comb == "linear" else 0.0, base=base)
        a = G.compile_batch([c], graph=False).run(tape, keep_paths=True)
        b = G.compile_batch([c], graph=True).run(tape, keep_paths=True)
        assert max((a.logW[t] - b.logW[t]).abs().max() for t in "BCJ") < 1e-9


def test_equivalence_suite_keys():
    c = cand({0: (("ratio", (1.0, 0)),), 2: (("restart", (1.0,)),)})
    out = SR.equivalence_suite([c], None, "cpu", n=4, T=200)[c.hash]
    assert {f"E{i}" for i in range(1, 11)} <= set(out)
    assert out["E5"]["res"]["pass_"] and out["E10"]["valid"] and "no_restart" in out["E6"]["res"]
    assert isinstance(out["E3"]["in_class"], bool)


def test_stage4_bootstrap_vectorised_at_scale():
    """648 cells x 1000 seeds x (5 finalists + 10 frontier members): one gather per chunk, no per-resample python loop."""
    import time

    import pandas as pd

    from shiftlab.hgxh2c import stats

    s4 = script("stage4_confirm")
    rng = np.random.default_rng(0)
    C, S = 648, 1000
    W = pd.DataFrame({"cell_id": np.repeat(np.arange(C), S), "seed": np.tile(np.arange(S), C)})
    for m in [f"f{i}" for i in range(5)] + [f"b{i}" for i in range(10)]:
        W[m] = (
            rng.normal(10, 3, C * S)
            + (0.2 if m.startswith("f") else 0.0)
            + np.repeat(rng.normal(0, 2, C), S)
        )
    s4._M.clear()
    t0 = time.perf_counter()
    res = [s4.boot(W, f"f{i}", f"b{j}", 4000, seed=1) for i in range(5) for j in range(10)]
    dt = time.perf_counter() - t0
    print(
        f"stage-4 bootstrap: 50 pairs x 4000 resamples at 648x1000 in {dt:.1f}s ({dt / 50:.2f}s per pair)"
    )
    assert all(0 < r["p"] <= 1 for r in res) and dt < 600, dt
    Ws = W[W.cell_id < 40].copy()
    ref = stats.paired_cluster_bootstrap(Ws, "f0", "b0", n_boot=2000, seed=0)
    new = s4.boot(Ws, "f0", "b0", 2000, seed=0, key="small")
    assert (
        abs(ref["mean"] - new["mean"]) < 1e-9
        and abs(ref["lo"] - new["lo"]) < 0.15
        and abs(ref["hi"] - new["hi"]) < 0.15
    )


def test_a6_score_is_min_over_members_of_cumulative_gain():
    """Three baselines, each best in a different cell: the A6 score is min_b mean(J_b - J_c) and beats the old per-cell-min score."""
    JP = np.array([[1.0, 5.0, 5.0], [5.0, 1.0, 5.0], [5.0, 5.0, 1.0]])  # member b is best in cell b
    Jc = np.array(
        [[2.0, 2.0, 2.0], [0.5, 0.5, 9.0]]
    )  # candidate 0 is worse than each member in its own cell
    dJ, bind = SR.min_member_gain(JP, Jc)
    want = np.array([min((JP[b] - Jc[i]).mean() for b in range(3)) for i in range(2)])
    assert np.allclose(dJ, want)
    old = (JP.min(0)[None] - Jc).mean(1)  # A5: gain against the per-cell oracle composite
    assert (dJ > old + 1e-12).all()  # strictly larger: the composite is not a deployable comparator
    assert (
        bind[0] == 0
    )  # member 0 is the binding one for candidate 0 (all members tie on mean J, argmin is the first)
    tabs = {
        "J": Jc,
        "harm": np.ones((2, 3)),
        "hit": np.ones((2, 3)),
        "fa": np.zeros((2, 3)),
        "null": np.zeros((2, 3)),
        "lab": np.ones((2, 3)),
        "runtime": np.zeros(2),
    }
    d = SR.summarise(tabs, JP, None, JP[:2])
    assert np.allclose(d.dJ, dJ) and np.allclose(d.dJ_sec, SR.min_member_gain(JP[:2], Jc)[0])


def test_registry_scoring_version_and_sidecar(tmp_path):
    import pandas as pd

    d = tmp_path / "registry.parquet"
    old = SR.Registry(d)
    old.append(
        "r0-c0", pd.DataFrame({"rung": [0], "hash": ["a"], "status": "evaluated", "dJ": [-1.0]})
    )
    (d / "_scoring_manifest.json").write_text(
        json.dumps({"a5_percell_min": ["part-r0-c0.parquet"]})
    )
    new = SR.Registry(d, prefix="a6-")
    new.append(
        "r0-c0", pd.DataFrame({"rung": [0], "hash": ["b"], "status": "evaluated", "dJ": [1.0]})
    )  # same logical name, no collision
    r = new.read().set_index("hash")
    assert (
        r.loc["a", "scoring"] == "a5_percell_min"
        and r.loc["b", "scoring"] == "a6_min_member_cumulative"
    )
    assert len(pd.read_parquet(d)) == 2  # the sidecar does not break dataset reads
