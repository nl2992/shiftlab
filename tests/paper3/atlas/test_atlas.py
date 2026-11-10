import math

import numpy as np
import pytest

from shiftlab.paper3.atlas.cells import design, validity
from shiftlab.paper3.atlas.certificate_stops import PrPlEBCS
from shiftlab.paper3.atlas.policies import MarkovBetEvidence
from shiftlab.paper3.atlas.runner import MAIN, REPAIR, run_one


def wsr_reference(ws, delta, lam_max=0.5):
    """Independent WSR (arXiv:2010.09686 eqs 13-15) CS by brute-force grid over m."""
    ms = np.linspace(0, 1, 2001)
    lo_run, hi_run = 0.0, 1.0
    s_w = 0.0
    ss = 0.0
    sl = slw = svp = 0.0
    out = []
    for t, w in enumerate(ws, 1):
        sig2 = (0.25 + ss) / t
        mu_prev = (0.5 + s_w) / t
        lam = min(math.sqrt(2 * math.log(2 / delta) / (sig2 * t * math.log(1 + t))), lam_max)
        psi = (-math.log(1 - lam) - lam) / 4
        sl += lam
        slw += lam * w
        svp += 4 * (w - mu_prev) ** 2 * psi
        s_w += w
        mu_t = (0.5 + s_w) / (t + 1)
        ss += (w - mu_t) ** 2
        # CS = {m : |sum lam (w-m)| <= log(2/delta) + sum v psi}; brute force on grid
        lhs = np.abs(slw - sl * ms)
        ok = ms[lhs <= math.log(2 / delta) + svp]
        lo_run, hi_run = max(lo_run, ok.min()), min(hi_run, ok.max())
        out.append((lo_run, hi_run))
    return out


def test_psi_E_fix_matches_reference_and_legacy_is_wider():
    rng = np.random.default_rng(1)
    ws = (rng.random(300) < 0.6).astype(float)
    ref = wsr_reference(ws, 0.05)
    a, b = PrPlEBCS(0.05), PrPlEBCS(0.05, legacy_psi=True)
    for i, w in enumerate(ws):
        a.update(w)
        b.update(w)
        assert abs(a.lo - ref[i][0]) < 1e-3 and abs(a.hi - ref[i][1]) < 1e-3
    assert (b.hi - b.lo) > 1.5 * (a.hi - a.lo)


def test_fixed_cs_covers():
    rng = np.random.default_rng(2)
    bad = 0
    for _ in range(300):
        cs = PrPlEBCS(0.05)
        for w in (rng.random(400) < 0.3).astype(float):
            cs.update(w)
            if not (cs.lo <= 0.3 <= cs.hi):
                bad += 1
                break
    assert bad / 300 <= 0.08


def markov_null_rate(mode, rho, rho_max, gap, n=400, nq=150, seed=3):
    rng = np.random.default_rng(seed)
    rej = 0
    for _ in range(n):
        ev = MarkovBetEvidence(mode, rho_max=rho_max, g_nom=gap)
        x = int(rng.random() < 0.5)
        t = 0
        for _k in range(nq):
            t += gap
            keep = rng.random() < rho**gap
            x = x if keep else int(rng.random() < 0.5)
            ev.update(t, x)
            if ev.log_e >= math.log(20):
                rej += 1
                break
    return rej / n


def test_gapaware_valid_under_markov_and_iid_gate_is_not():
    assert markov_null_rate("gapaware", 0.9, 0.95, 5) <= 0.08
    assert markov_null_rate("iid", 0.9, 0.95, 5) > 0.2
    assert markov_null_rate("gapaware", 0.99, 0.95, 5) > 0.08  # misdeclared bound breaks validity


@pytest.mark.parametrize("cid", [2, 3])
def test_accounting_identity_budget_and_pairing(cid):
    cell = design()[cid]
    rows = run_one(
        cell,
        0,
        MAIN + REPAIR + ["iid_gate", "discern_legacy", "edetector_cal", "cusum_cal"],
        False,
        1,
    )
    for r in rows:  # identity asserted inside episode_metrics; budget:
        assert r["n_q"] <= cell.budget
    j = {r["method"]: r["J"] for r in rows}
    assert j["never_switch"] == pytest.approx(
        run_one(cell, 0, ["never_switch"], False, 1)[0]["J"]
    )  # deterministic pairing


def test_design_and_validity_table():
    cells = design()
    assert len(cells) == 32 and {c.rho for c in cells} == {0.0, 0.5, 0.8, 0.95}
    assert validity(cells[3], "gated_mope").startswith("INVALID")
    assert validity(cells[3], "c1_gapaware_rho80").startswith("INVALID")
    assert validity(cells[0], "c1_gapaware").startswith("valid")
