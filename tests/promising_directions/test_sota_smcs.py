"""Tests for the SMCS port: hand-computed steps, multiplicity, R-reference agreement, validity."""

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota/competitors"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions"))

import smcs
from simulator import (
    Event,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

VENDOR = ROOT / "vendor_sota/smcs"
RSCRIPT = shutil.which("Rscript") or "/opt/homebrew/bin/Rscript"
HAVE_R = Path(RSCRIPT).exists() and (VENDOR / "Simulation_1/SMCS/Simulation1.R").exists()

# Reference harness. It executes the AUTHOR'S lines Simulation1.R:77-124 unmodified (read from the
# vendored file at run time) on a supplied loss matrix. Only the data-generation and CRPS blocks
# (lines 28-70) are replaced, because they need the missing package scoringRules; the 0/1 bound
# c = 1 stands in for them. For m = 2 the author's ``colMeans(E[i, -i,])`` fails (the subset drops
# to a vector), so ``drop = FALSE`` is inserted; m >= 3 runs literally.
R_HARNESS = r"""
args <- commandArgs(trailingOnly = TRUE)
vendor <- args[1]; infile <- args[2]; outfile <- args[3]; alpha <- as.numeric(args[4])
library(jsonlite)
source(file.path(vendor, "Simulation_1/SMCS/Adjusting.R"))
L <- as.matrix(read.csv(infile, header = FALSE))
n <- nrow(L); m <- ncol(L)
cc <- matrix(1, m, m); lambda <- 1 / (2 * cc)
ind_sup_model <- 1
src <- readLines(file.path(vendor, "Simulation_1/SMCS/Simulation1.R"))
body <- src[77:124]
if (m == 2) body <- sub("E[i, -i,]", "E[i, -i, , drop = FALSE]", body, fixed = TRUE)
invisible(capture.output(eval(parse(text = body))))
write_json(list(E_adj = t(E_adj), members = lapply(1:n, function(t) MCS_e[[t]])),
           outfile, digits = NA, auto_unbox = FALSE)
"""


def run_r(losses: np.ndarray, alpha: float, tmp: Path):
    (tmp / "h.R").write_text(R_HARNESS)
    np.savetxt(tmp / "L.csv", losses, delimiter=",", fmt="%.17g")
    subprocess.run(
        [
            RSCRIPT,
            str(tmp / "h.R"),
            str(VENDOR),
            str(tmp / "L.csv"),
            str(tmp / "o.json"),
            str(alpha),
        ],
        check=True,
        capture_output=True,
    )
    import json

    out = json.loads((tmp / "o.json").read_text())
    return np.array(out["E_adj"], dtype=float), [
        list(map(int, np.atleast_1d(s))) for s in out["members"]
    ]


def fixed_losses(T, m, seed, bad=None):
    """Deterministic 0/1 losses; model ``bad`` is worse."""
    rng = np.random.default_rng(seed)
    err = np.full(m, 0.3)
    if bad is not None:
        err[bad] = 0.6
    return (rng.random((T, m)) < err).astype(float)


# ---------------------------------------------------------------------------- hand-computed
def test_hand_computed_step_three_models():
    # L = (1, 0, 0), c = 1, lambda = 1/2: E01 = E02 = 1.5, E10 = E20 = 0.5, E12 = E21 = 1.
    s = smcs.SMCSInference(3, alpha=0.1)
    s.update_losses(np.array([1.0, 0.0, 0.0]), c=1.0)
    np.testing.assert_allclose(s.E[0, [1, 2]], 1.5)
    np.testing.assert_allclose(s.E[[1, 2], 0], 0.5)
    np.testing.assert_allclose([s.E[1, 2], s.E[2, 1]], 1.0)
    ee = smcs.arithmetic_mean_evalue(s.E)
    np.testing.assert_allclose(ee, [1.5, 0.75, 0.75])
    # closure: sorted (0.75, 0.75, 1.5); model 0 -> min((1.5+.75)/2, (1.5+1.5)/3) = 1.0
    np.testing.assert_allclose(s.e_adj, [1.0, 0.75, 0.75])
    assert s.members.all()  # first step is exempt, and nothing reaches 1/alpha anyway


def test_strict_threshold_and_nesting():
    prev = np.array([True, True, False])
    out = smcs.confidence_set_step(prev, np.array([10.0, 9.99, 0.1]), alpha=0.1)
    # E_adj == 1/alpha is excluded (strict <); an excluded model (index 2) never returns
    np.testing.assert_array_equal(out, [False, True, False])


# ---------------------------------------------------------------------------- multiplicity
def test_closure_adjust_properties():
    rng = np.random.default_rng(3)
    for _ in range(50):
        e = rng.exponential(2.0, size=rng.integers(2, 9))
        a = smcs.closure_adjust(e)
        assert (a <= e + 1e-12).all()  # adjustment never inflates evidence
        # preserves the ordering of the raw e-values
        assert (np.argsort(a, kind="stable") == np.argsort(e, kind="stable")).all() or np.allclose(
            np.sort(a), a[np.argsort(e, kind="stable")]
        )
    np.testing.assert_allclose(smcs.closure_adjust(np.full(5, 3.0)), 3.0)  # ties unchanged
    # smallest e-value is never adjusted (R's [1:0] quirk), the largest of two is averaged
    np.testing.assert_allclose(smcs.closure_adjust(np.array([20.0, 4.0])), [12.0, 4.0])
    np.testing.assert_allclose(smcs.closure_adjust(np.array([7.0])), [7.0])


def test_multiplicity_makes_exclusion_harder_than_the_raw_mean():
    # one dominant model, two weak: raw mean e-value of the worst exceeds 1/alpha before the
    # adjusted one does, so the adjusted set excludes later
    losses = np.array([[1.0, 0.0, 0.0]] * 12)
    s = smcs.SMCSInference(3, alpha=0.1)
    raw_first = adj_first = None
    for t in range(12):
        s.update_losses(losses[t])
        if raw_first is None and smcs.arithmetic_mean_evalue(s.E)[0] >= 10:
            raw_first = t
        if adj_first is None and not s.members[0]:
            adj_first = t
    assert raw_first is not None and adj_first is not None and adj_first >= raw_first


# ---------------------------------------------------------------------------- R agreement
@pytest.mark.skipif(not HAVE_R, reason="Rscript or vendor_sota/smcs not available")
@pytest.mark.parametrize("m,alpha,bad", [(3, 0.1, 2), (4, 0.05, 1), (2, 0.1, 1), (3, 0.5, None)])
def test_matches_author_r_code(tmp_path, m, alpha, bad):
    L = fixed_losses(300, m, seed=11 + m, bad=bad)
    r_eadj, r_members = run_r(L, alpha, tmp_path)
    py_eadj, py_mem = smcs.run_native(L, alpha, c=1.0)
    # R's t = 1 column: E_adj exists but the set is the full set by construction
    np.testing.assert_allclose(py_eadj, r_eadj.reshape(py_eadj.shape), rtol=1e-12, atol=0)
    for t in range(L.shape[0]):
        assert sorted(np.flatnonzero(py_mem[t]) + 1) == sorted(r_members[t]), (
            f"set differs at t={t}"
        )
    # non-degenerate: the comparison must have seen an exclusion in the cases built to cause one
    if bad is not None:
        assert not py_mem[-1].all()


def test_golden_matches_recorded_r_output():
    # Recorded from the R run of Simulation1.R:77-124 on fixed_losses(300, 3, seed=14, bad=2),
    # alpha = 0.1 (see report). Guards the port when Rscript is absent.
    L = fixed_losses(300, 3, seed=14, bad=2)
    e_adj, mem = smcs.run_native(L, 0.1)
    assert mem[-1].tolist() == GOLDEN["members"]
    np.testing.assert_allclose(e_adj[-1], GOLDEN["e_adj"], rtol=1e-12)
    assert GOLDEN["first_exclusion_t"] == int(np.flatnonzero(~mem[:, 2].astype(bool))[0])


GOLDEN = {
    "members": [True, True, False],
    "e_adj": [1.9932226830932e-08, 3.98644536618641e-09, 1371438388.79758],
    "first_exclusion_t": 13,
}


# ---------------------------------------------------------------------------- validity on a null
def test_time_uniform_coverage_on_a_null_stream():
    # Two exchangeable models: E[d] = 0, so both H_01 and H_10 hold and no model should ever be
    # excluded except with probability <= alpha, uniformly over time.
    alpha, reps, T = 0.1, 600, 400
    rng = np.random.default_rng(5)
    ever = 0
    for _ in range(reps):
        L = (rng.random((T, 2)) < 0.3).astype(float)
        _, mem = smcs.run_native(L, alpha)
        ever += not mem[-1].all()  # the set is nested, so the last row records any exclusion
    rate = ever / reps
    assert rate <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / reps)


def test_selective_stream_null_coverage_with_weighting():
    # Same null under sampled feedback with the B3+ pacer: the weighted construction must not be
    # anti-conservative.
    alpha, reps, T = 0.1, 150, 500
    ever = 0
    for r in range(reps):
        rng = np.random.default_rng(100 + r)
        y = rng.integers(0, 2, T)
        wrong0 = rng.random(T) < 0.25
        wrong1 = rng.random(T) < 0.25
        preds = np.stack([np.where(wrong0, 1 - y, y), np.where(wrong1, 1 - y, y)], 1)
        pol = smcs.SMCSDeploymentPolicy(2, policy_rng(0, r, "smcs"), alpha=alpha)
        run_episode(
            pol,
            model_predictions=preds,
            labels=y,
            delay=3,
            budget=120,
            label_price=0.0,
            switch_cost=0.0,
            trace=False,
        )
        ever += not pol.inference.members.all()
    assert ever / reps <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / reps)


# ---------------------------------------------------------------------------- loss bounds
@pytest.mark.parametrize("q", [0.05, 0.1, 0.5, 1.0])
def test_weighting_preserves_the_loss_bound(q):
    for losses in ([0, 1], [1, 0], [1, 1], [0, 0]):
        d, lam = smcs.weighted_pair_inputs(np.array(losses), q)
        assert np.abs(d).max() <= 1.0 / q + 1e-12  # weighted difference leaves [-1, 1]
        f = 1.0 + lam * d
        assert f.min() >= 0.5 - 1e-12 and f.max() <= 1.5 + 1e-12  # but the factor does not
        # unbiasedness under the null-style check: E over Z of the factor is 1 + q*d_raw/2
        raw = losses[0] - losses[1]
        assert np.isclose(q * f[0, 1] + (1 - q) * 1.0, 1.0 + q * raw / 2.0)


def test_unscaled_native_lambda_would_break_the_bound():
    # the construction we did NOT adopt: native lambda = 1/2 on weighted differences
    d, _ = smcs.weighted_pair_inputs(np.array([0, 1]), 0.05)  # d_01 = -20
    assert (1.0 + 0.5 * d).min() < 0  # negative "wealth": not an e-process


def test_policy_factors_stay_in_range_end_to_end():
    rng = np.random.default_rng(1)
    T = 600
    y = rng.integers(0, 2, T)
    preds = np.stack(
        [np.where(rng.random(T) < 0.3, 1 - y, y), np.where(rng.random(T) < 0.2, 1 - y, y)], 1
    )
    pol = smcs.SMCSDeploymentPolicy(2, policy_rng(0, 0, "smcs"))
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=2, budget=80, label_price=0.0, switch_cost=0.0
    )
    assert 0.5 - 1e-12 <= pol.inference.min_factor
    assert check_budget_feasible(res, 80) == [] and check_no_future_access(res, 2) == []


# ---------------------------------------------------------------------------- acquisition
def test_acquisition_matches_b3_plus_p7a():
    b3p = pytest.importorskip("b3_plus_policy")
    T, delay, budget = 400, 5, 60
    p = b3p.b1.Params(T=T, delay=delay)
    rng = np.random.default_rng(7)
    y = rng.integers(0, 2, T)
    preds = np.stack(
        [np.where(rng.random(T) < 0.2, 1 - y, y), np.where(rng.random(T) < 0.3, 1 - y, y)], 1
    )
    l0, l1 = (preds[:, 0] != y).astype(float), (preds[:, 1] != y).astype(float)
    u = policy_rng(0, 0, "smcs").random(T)  # the policy draws exactly one uniform per event
    out, objs = b3p.run_plus_policies(
        l0[:, None],
        l1[:, None],
        u[:, None],
        budget,
        0.0,
        p.cq,
        p,
        [b3p.PlusParams(variant="P7a")],
        trace=True,
        return_objs=True,
    )
    tr = objs["P7a"].tr
    pol = smcs.SMCSDeploymentPolicy(2, policy_rng(0, 0, "smcs"))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=y,
        delay=delay,
        budget=budget,
        label_price=0.0,
        switch_cost=0.0,
    )
    asked = np.array([r["requested"] for r in res.records])
    np.testing.assert_array_equal(asked, tr["ask"][:, 0].astype(int))
    q_ours = np.array([r["query_probability"] for r in res.records])
    np.testing.assert_allclose(q_ours[asked == 1], tr["q"][asked == 1, 0], rtol=0, atol=1e-15)
    assert asked.sum() == out["P7a"]["queries"][0]


# ---------------------------------------------------------------------------- deployment rule
def _drive(policy, preds, y, delay=1, budget=10**6):
    return run_episode(
        policy,
        model_predictions=preds,
        labels=y,
        delay=delay,
        budget=budget,
        label_price=0.0,
        switch_cost=0.0,
    )


def test_deployment_retains_incumbent_until_excluded_and_is_separate():
    assert not hasattr(smcs.SMCSInference, "predict")  # the inference component is not a policy
    T = 400
    y = np.zeros(T, dtype=int)
    preds = np.stack([np.ones(T, dtype=int), np.zeros(T, dtype=int)], 1)  # incumbent always wrong
    pol = smcs.SMCSDeploymentPolicy(2, policy_rng(0, 0, "smcs"), alpha=0.05)
    res = _drive(pol, preds, y, budget=10**6)
    dep = np.array([r["deployed_model"] for r in res.records])
    first_switch = int(np.argmax(dep == 1))
    assert dep[0] == 0 and first_switch > 0  # retained until evidence accumulated
    assert (dep[first_switch:] == 1).all()
    assert not pol.inference.members[0]


def test_cumulative_evidence_is_not_current_regime_evidence():
    # model 1 is worse for 300 rounds, then better for 600: SMCS cannot readmit it
    T1, T2 = 300, 600
    y = np.zeros(T1 + T2, dtype=int)
    p0 = np.r_[np.zeros(T1), np.ones(T2) * 1].astype(int)  # incumbent right, then wrong
    p1 = np.r_[np.ones(T1), np.zeros(T2)].astype(int)  # challenger wrong, then right
    L = np.stack([(p0 != y), (p1 != y)], 1).astype(float)
    _, mem = smcs.run_native(L, alpha=0.05)
    first_out_1 = int(np.flatnonzero(~mem[:, 1])[0])
    assert first_out_1 < T1  # challenger excluded in regime 1
    assert not mem[-1, 1]  # and still excluded at the end, though it is best now
    # nested: no model ever re-enters
    assert (mem[1:] <= mem[:-1]).all()


def test_determinism_and_state_roundtrip():
    rng = np.random.default_rng(2)
    T = 300
    y = rng.integers(0, 2, T)
    preds = np.stack(
        [np.where(rng.random(T) < 0.4, 1 - y, y), np.where(rng.random(T) < 0.1, 1 - y, y)], 1
    )
    a = _drive(smcs.SMCSDeploymentPolicy(2, policy_rng(1, 2, "x")), preds, y, delay=2, budget=50)
    b = _drive(smcs.SMCSDeploymentPolicy(2, policy_rng(1, 2, "x")), preds, y, delay=2, budget=50)
    assert a.records == b.records
    pol = smcs.SMCSDeploymentPolicy(2, policy_rng(1, 2, "x"))
    _drive(pol, preds[:150], y[:150], delay=2, budget=50)
    snap = pol.state_dict()
    pol2 = smcs.SMCSDeploymentPolicy(2, policy_rng(9, 9, "other"))
    pol2.load_state_dict(snap)
    assert pol2.state_dict()["inference"] == snap["inference"]
    assert pol2.deployed == pol.deployed
    ev = Event(event_id=0, t=150, horizon=T, model_predictions=np.array([0, 1]))
    assert pol2.request_labels(ev, 10).requested == pol.request_labels(ev, 10).requested
