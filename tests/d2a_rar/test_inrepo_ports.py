"""WP1e regression tests for the in-repo comparator ports.

Three kinds of evidence per ported method (see docs/d2a_rar/baselines/INREPO_PORTS.md):
  A. source identity   : the port equals ``git show <ref>:<path>`` apart from the stated import rewrite;
  B. bit-for-bit       : the ported class and the class imported from a temporary ``git show`` extraction
                         give identical per-seed results on the same streams;
  C. documented cell   : a small-seed rerun of a cell from the source branch's results document agrees
                         with the documented number within Monte-Carlo error (subset of the documented seeds).
Plus contract checks for ``adapters_inrepo`` (leak guards, audit, budgets, null keys).
Tests that need a git ref skip when the ref is unavailable (e.g. shallow clone).
"""

from __future__ import annotations

import ast
import importlib
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
GAVER = "origin/research/gave-r-2026-11-06"
SPRINT = "origin/codex/sprint2-leaderboards"
INREPO = ROOT / "src/shiftlab/sota/inrepo"


def _git_show(ref: str, path: str) -> str | None:
    p = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return p.stdout if p.returncode == 0 else None


needs_gaver = pytest.mark.skipif(
    _git_show(GAVER, "src/shiftlab/gaver/pave.py") is None, reason=f"{GAVER} not available"
)
needs_sprint = pytest.mark.skipif(
    _git_show(SPRINT, "scripts/failure_atlas_v2/restart_monitor.py") is None,
    reason=f"{SPRINT} not available",
)

GAVER_FILES = ("gapmix", "pave", "freshcheck", "integrated", "erb_port")


# ------------------------------------------------------------------------------------ A. source identity
@needs_gaver
@pytest.mark.parametrize("name", GAVER_FILES)
def test_port_source_identical(name):
    src = _git_show(GAVER, f"src/shiftlab/gaver/{name}.py")
    port = (INREPO / f"{name}.py").read_text(encoding="utf-8").splitlines(keepends=True)
    assert port[0].startswith("# PORTED UNCHANGED") and f"src/shiftlab/gaver/{name}.py" in port[1]
    body = "".join(port[4:])
    assert body == src.replace("shiftlab.gaver", "shiftlab.sota.inrepo")


@needs_sprint
def test_rmm_blocks_verbatim():
    port = (INREPO / "rmm.py").read_text(encoding="utf-8")
    for ref_path, classes in (
        (
            "scripts/failure_atlas_v2/restart_monitor.py",
            ("HorizonWeightedPacer", "MixtureSRDetector"),
        ),
        (
            "scripts/promising_directions/sota/competitors/controls.py",
            ("PacedDisagreementAcquisition",),
        ),
    ):
        text = _git_show(SPRINT, ref_path)
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in classes:
                assert ast.get_source_segment(text, node) in port, node.name


# ------------------------------------------------------------------------------------ B. bit-for-bit
@pytest.fixture(scope="module")
def orig(tmp_path_factory):
    """Temporary extraction of the original gaver package (import path rewritten only)."""
    if _git_show(GAVER, "src/shiftlab/gaver/pave.py") is None:
        pytest.skip(f"{GAVER} not available")
    pkg = tmp_path_factory.mktemp("orig") / "gaver_orig"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    for n in ("gapmix", "pave", "freshcheck", "integrated", "erb_port"):
        (pkg / f"{n}.py").write_text(
            _git_show(GAVER, f"src/shiftlab/gaver/{n}.py").replace("shiftlab.gaver", "gaver_orig"),
            encoding="utf-8",
        )
    sys.path.insert(0, str(pkg.parent))
    try:
        yield {n: importlib.import_module(f"gaver_orig.{n}") for n in GAVER_FILES}
    finally:
        sys.path.remove(str(pkg.parent))
        for k in [k for k in sys.modules if k.startswith("gaver_orig")]:
            del sys.modules[k]


def _run(cell, method, seed):
    from shiftlab.dive import failure_atlas as fa

    stream, cfg = fa.make_stream(cell, seed), cell.config(seed)
    r = fa.run_for(cell, stream, method, cfg)
    return (tuple(r.actions.tolist()), float(r.cost), int(r.queries), int(r.promotions))


def _f3_cell(rho, bt, d=10):
    from shiftlab.dive import failure_atlas as fa

    return fa.Family3CellSpec(rho, 0.3, 0.6, "strong", "harmful", d, bt, T=1000)


def _f1_cell(cid="on0.6_L1_strong_harmful_d50_b0.05_s0.1"):
    from shiftlab.dive import failure_atlas as fa

    return {c.cell_id: c for c in fa.all_cells(1000)}[cid]


@needs_gaver
def test_bitforbit_gapmix_gates(orig):
    from shiftlab.sota.inrepo import gapmix as port

    cell = _f3_cell(0.5, 0.1)
    for name in ("exact0.8_s4", "env0.8_s4", "thin10_s4", "mlr_default8"):
        for sd in (101000001, 101000002):
            assert _run(cell, port.build_gate(name), sd) == _run(
                cell, orig["gapmix"].build_gate(name), sd
            ), name


@needs_gaver
def test_bitforbit_freshcheck_erb_twophase(orig):
    from shiftlab.sota.inrepo import freshcheck as pf

    def run(mod, name, seed, cell):
        m = mod.make_method(name)
        res = mod.run(mod.make_stream(cell, seed), m, cell.config(seed))
        return (tuple(res.actions.tolist()), float(res.cost), int(res.queries))

    for kind in ("persistent", "reversal"):
        cell = pf.Wp3Cell(kind, 0.2, 10)
        for name in ("fresh_reserve", "fresh_noreserve", "erb", "two_phase", "existing_cusum"):
            sd = 101120000 + 7
            assert run(pf, name, sd, cell) == run(
                orig["freshcheck"], name, sd, orig["freshcheck"].Wp3Cell(kind, 0.2, 10)
            ), (kind, name)


@needs_gaver
def test_bitforbit_pave_and_delay_gated_pave(orig):
    from shiftlab.sota.inrepo import integrated as pi
    from shiftlab.sota.inrepo import pave as pp

    cell = _f1_cell()  # d=50, B=50: delay gate ON (d >= 2T/(B+2))
    sd = 101090003
    a = _run(cell, pp.PaveMethod(pp.PaveParams(kappa=0.1, q=0.03)), sd)
    b = _run(cell, orig["pave"].PaveMethod(orig["pave"].PaveParams(kappa=0.1, q=0.03)), sd)
    assert a == b
    assert _run(cell, pi.build("gaver:gapmix:pave"), sd) == _run(
        cell, orig["integrated"].build("gaver:gapmix:pave"), sd
    )
    assert pi.pave_active(cell.config(sd)) and not pi.pave_active(
        _f3_cell(0.0, 0.1, d=10).config(1)
    )


# ------------------------------------------------------------------------------------ C. documented cells
def _binom_ok(k, n, k_doc, n_doc=500):
    """k successes in the first n of the documented n_doc streams (same seeds)."""
    p = k_doc / n_doc
    return k <= k_doc and abs(k - n * p) <= 4 * math.sqrt(n * max(p * (1 - p), 1.0 / n_doc)) + 1.5


def _null_fp(name, rho, bt, idx, n):
    """docs/gaver/10_GAPMIX_RESULTS.md 1.4 protocol: boundary-null twin, seeds 101000000 + 1000*idx + i."""
    from shiftlab.dive import failure_atlas as fa
    from shiftlab.sota.inrepo import gapmix as gm

    cell = _f3_cell(rho, bt).null_twin()
    k = 0
    for i in range(n):
        sd = 101000000 + 1000 * idx + i
        r = fa.run_for(cell, fa.make_stream(cell, sd), gm.build_gate(name), cell.config(sd))
        k += int((r.fp_regime or 0) > 0)
    return k


# documented k/500 (10_GAPMIX_RESULTS.md section 1.4 table): (method, rho, B/T, null-cell index) -> k
GAPMIX_DOC = {
    ("iid_s4", 0.8, 0.25, 5): 202,
    ("thin10_s4", 0.8, 0.25, 5): 21,
    ("mlr_default8", 0.8, 0.25, 5): 4,
    ("exact0.8_s4", 0.8, 0.1, 4): 29,
    ("env0.8_s4", 0.8, 0.1, 4): 24,
    ("iid_s4", 0.8, 0.1, 4): 36,
}


@needs_gaver
@pytest.mark.parametrize(
    "key,n",
    [
        (("iid_s4", 0.8, 0.25, 5), 60),
        (("thin10_s4", 0.8, 0.25, 5), 60),
        (("mlr_default8", 0.8, 0.25, 5), 40),
        (("exact0.8_s4", 0.8, 0.1, 4), 40),
        (("env0.8_s4", 0.8, 0.1, 4), 40),
        (("iid_s4", 0.8, 0.1, 4), 60),
    ],
)
def test_gapmix_null_cell_matches_documented(key, n):
    name, rho, bt, idx = key
    k = _null_fp(name, rho, bt, idx, n)
    assert _binom_ok(k, n, GAPMIX_DOC[key]), (key, k, n, GAPMIX_DOC[key])


@needs_gaver
def test_pave_regression_cell_matches_documented():
    """docs/gaver/20_PAVE_RESULTS.md, cell on0.6_L1_strong_harmful_d50_b0.05_s0.1, seeds 101090000+i (first 8 of 60).

    Documented (n=60, PAVE-full reserve on, kappa .1, q .03): DSS 0.4014, PAVE 0.3818, episode_front 0.3876,
    PAVE-DSS = -0.0196 [-0.0364, -0.0046]. Per-seed sd of the paired difference ~0.066 (measured), so the
    8-seed mean has se ~0.023; accept within 3 se of the documented difference and 3 se (0.07/sqrt(8)) on levels."""
    from shiftlab.dive import failure_atlas as fa
    from shiftlab.sota.inrepo import atlas_methods as am
    from shiftlab.sota.inrepo.pave import PaveMethod, PaveParams

    cell, n = _f1_cell(), 8
    cost = {"dss": [], "pave": [], "episode_front": []}
    for i in range(n):
        sd = 101090000 + i
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        for k, m in (
            ("dss", am.build("dss")),
            ("pave", PaveMethod(PaveParams(kappa=0.1, q=0.03))),
            ("episode_front", am.build("episode_front")),
        ):
            r = fa.run_for(cell, stream, m, cfg)
            assert r.queries <= cfg.B
            cost[k].append(r.cost / cell.T)
    se = 0.07 / math.sqrt(n)
    for k, doc in (("dss", 0.4014), ("pave", 0.3818), ("episode_front", 0.3876)):
        assert abs(np.mean(cost[k]) - doc) <= 3 * se, (k, np.mean(cost[k]), doc)
    diff = np.array(cost["pave"]) - np.array(cost["dss"])
    assert abs(diff.mean() - (-0.0196)) <= 3 * 0.066 / math.sqrt(n)


@needs_gaver
def test_freshcheck_family_persistent_and_null_match_documented():
    """docs/gaver/30_FRESHCHECK_RESULTS.md Table A (persistent kind, mean J/T over onset{.2,.5} x d{1,10}) and
    the boundary-null false-promotion count (0/1000). 4 cells x 4 seeds (seeds 101120000 + 100*ci + i)."""
    from shiftlab.sota.inrepo import freshcheck as fc

    doc = {
        "existing_cusum": 0.507,
        "fresh_reserve": 0.467,
        "fresh_noreserve": 0.418,
        "erb": 0.418,
        "two_phase": 0.569,
    }
    vals = {k: [] for k in doc}
    ci = 0
    for onset in (fc.EARLY, fc.LATE):
        for d in (1, 10):
            for i in range(4):
                for r in fc.run_cell_seed(
                    fc.Wp3Cell("persistent", onset, d), 101120000 + 100 * ci + i, tuple(doc)
                ):
                    vals[r["method"]].append(r["J"])
            ci += 1
    for k, v in doc.items():
        assert abs(np.mean(vals[k]) - v) <= 0.06, (
            k,
            np.mean(vals[k]),
            v,
        )  # per-stream se ~0.07 / sqrt(16)=0.018
    # E_rb without reserve and FreshCheck-noreserve are documented as indistinguishable
    assert abs(np.mean(vals["erb"]) - np.mean(vals["fresh_noreserve"])) < 0.02
    fp = 0
    for i in range(10):
        for r in fc.run_cell_seed(
            fc.Wp3Cell("null", d=10), 101130000 + 1000 + i, ("fresh_reserve", "erb", "two_phase")
        ):
            fp += r["fp"]
    assert (
        fp <= 1
    )  # documented 10/1000 for erb, 0/1000 for fresh/two_phase; P(>=2 in 10) < 1e-3 at 1%


def test_rmm_detector_semantics():
    """MixtureSRDetector: total prior mass one => all-ones input alarms; alternating signs never do at alpha .1."""
    from shiftlab.sota.inrepo.rmm import MixtureSRDetector

    det = MixtureSRDetector(0.1, 100, gap=10)
    n = 0
    while not det.update(+1):
        n += 1
        assert n < 200
    assert n < 60
    det = MixtureSRDetector(0.1, 100, gap=10)
    assert not any(det.update(1 if i % 2 == 0 else -1) for i in range(400))


# ------------------------------------------------------------------------------------ contract adapter checks
def _env(label_cap=60, cost="balanced", obs="shadow"):
    from shiftlab.bench.contract import BudgetSpec, ClockSpec, EnvSpec, load_cost_vectors

    return EnvSpec(
        T=1000,
        costs=load_cost_vectors()[cost],
        budget=BudgetSpec(label_cap=label_cap),
        clocks=ClockSpec(retrain_duration=20),
        obs_mode=obs,
        allowed_actions=("query", "continue", "switch", "rollback"),
    )


FAST = (
    "gapmix:thin10_s4",
    "gapmix:mlr_default8",
    "markov_lr_gate",
    "episode_front",
    "dss",
    "gaver:dss:pave",
    "freshcheck:fresh_reserve",
    "erb",
    "two_phase",
    "page_cusum_default",
    "rmm_detector",
)


def test_adapters_run_audited_and_budgeted():
    from shiftlab.bench.contract import load_family, run_paired
    from shiftlab.bench.contract.adapters_inrepo import ADAPTERS

    env = _env()
    spec = load_family("iid_shift_d10")
    pr = run_paired(
        {n: (lambda n=n: ADAPTERS[n].build(env)) for n in FAST},
        spec,
        env,
        seeds=[110900000 + i for i in range(2)],
        on_violation="raise",
        verify=True,
    )
    for n in FAST:
        for r in pr.runs[n]:
            assert math.isfinite(r.J) and r.counts["N_q"] <= env.budget.label_cap
            assert not r.leak_attempts
            assert (
                r.counts["N_r"] == 0 and r.counts["N_a"] == 0
            )  # vocabulary: query/switch/rollback only


def test_adapter_metadata_matches_null_registry():
    from shiftlab.bench.contract.adapters_inrepo import ADAPTERS, NOT_PORTED

    reg = yaml.safe_load(
        (ROOT / "docs/d2a_rar/registry/null_assumptions.yaml").read_text(encoding="utf-8")
    )
    nulls = {e["id"]: e["target_null"] for e in reg["entries"]}
    norm = {"absolute_risk": "abs_risk", "economic": "none"}
    for n, ad in list(ADAPTERS.items()) + list(NOT_PORTED.items()):
        assert ad.port_status in ("COMMON_CONTRACT_PORT", "NOT_PORTED_TO_COMMON_CONTRACT")
        if ad.registry_id:
            assert ad.registry_id in nulls, (n, ad.registry_id)
            assert norm.get(nulls[ad.registry_id], nulls[ad.registry_id]) == ad.claimed_null, (
                n,
                ad.claimed_null,
            )
    for n in ("h2c", "pprm", "e_rb_sprint"):
        with pytest.raises(NotImplementedError):
            NOT_PORTED[n].build(_env())


def test_adapter_requires_shadow_mode():
    from shiftlab.bench.contract.adapters_inrepo import ADAPTERS

    pol = ADAPTERS["episode_front"].build(_env(obs="deployed"))
    with pytest.raises(NotImplementedError):
        pol.reset(_env(obs="deployed"))


def test_atlas_adapter_matches_native_harness_on_clean_stream():
    """On a contract stream with constant delay d, no missingness and shadow labels, the adapter must issue exactly
    the native method's action/query sequence (the contract only re-routes the I/O)."""
    from shiftlab.bench.contract import (
        BudgetSpec,
        ClockSpec,
        EnvSpec,
        Simulator,
        load_cost_vectors,
        load_family,
        make_stream,
    )
    from shiftlab.bench.contract.adapters_inrepo import AtlasMethodPolicy
    from shiftlab.dive.switching_explore import Config
    from shiftlab.sota.inrepo import atlas_methods as am

    spec = load_family("iid_shift_d10")
    env = EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()["label_cheap"],
        budget=BudgetSpec(label_cap=100),
        clocks=ClockSpec(retrain_duration=20),
        allowed_actions=("query", "continue", "switch", "rollback"),
    )
    st = make_stream(spec, 110900007)
    pol = AtlasMethodPolicy("episode_front", lambda: am.build("episode_front"), declared_delay=10)
    res = Simulator(st, env, on_violation="raise").run(pol)
    # replay natively from the labels the contract delivered (audit = evaluator side; test code only)
    cfg = Config(T=env.T, B=100, d=10, c=env.costs.c_q, s=env.costs.c_s, h=env.hurdle, alpha=0.1)
    m = am.build("episode_front")
    m.start(cfg)
    by_release: dict[int, list[int]] = {}
    for rec in res.audit.of("release"):
        by_release.setdefault(rec["delivered_t"], []).append(rec["label_round"])
    assert by_release  # labels were released
    q_native, a_native = [], []
    for t in range(1, env.T + 1):
        rel = tuple(
            (lr, float(st.loss_cand[lr - 1] - st.loss_inc[lr - 1]))
            for lr in sorted(by_release.get(t, []))
        )
        a, q = m.step(t, rel)
        q_native.append(int(q))
        a_native.append(a)
    q_contract = [0] * env.T
    for rec in res.audit.of("request"):
        q_contract[rec["t"] - 1] = 1
    assert q_native == q_contract
    assert pol.n_revoked == 0
    # model path of the contract run equals the native action path shifted by nothing (lag-0 deployments)
    assert list(res.model_path) == a_native
