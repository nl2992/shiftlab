"""G1 analytic growth check: exact per-event log-growth of IPW betting e-processes.

For each arm the increment is Z = -eps + c*1[query]/q on a disagreement (gated) or on every
event (uniform), with support bound B and stake grid s*Z/B. Growth is E log(1+s Z/B) maximised over
the registered stakes, computed by enumerating the query coin exactly (no simulation of coins).
"""
import numpy as np
from scipy.special import ndtr

from shiftlab.decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from shiftlab.dive.experiment import _binary_cost, _synthetic_label_costs

STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
EPS = 0.1


def growth(values_if_query, q, values_if_not, bound):
    """max over stakes of mean_t[q_t log(1+s v_q/B) + (1-q_t) log(1+s v_n/B)]."""
    best = -1e9
    for s in STAKES:
        g = np.mean(q * np.log1p(s * values_if_query / bound) + (1 - q) * np.log1p(s * values_if_not / bound))
        best = max(best, g)
    return best


def seed_ratio(seed, r):
    scen = next(s for s in SCENARIOS if s.name == "boundary_local_harm")
    base = ExperimentConfig(n=3200, d=16, evaluation_seeds=1, calibration_seeds=2, calibration_start=800,
                            window=64, stride=32, alpha=0.05, eprocess_epsilon=0.1, seed_offset=seed,
                            change_fraction=0.5, device="cpu")
    _, frame, oracle, timing = _generate(scen, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    ref = _source_action(x, scen)
    act = deployed != ref
    tar = _synthetic_label_costs(x)
    c = _binary_cost(deployed, y, scen.fn_cost, scen.fp_cost) - _binary_cost(ref, y, scen.fn_cost, scen.fp_cost)
    post = slice(1600, 3200)
    A, C = act[post], c[post]
    qD = min(1.0, r * tar[400:800].mean() / max((act[400:800] * tar[400:800]).mean(), 1e-6))
    # gated HT, fixed rate: agreements are known zero-cost -> value -eps; disagreements query w.p. qD
    vq = np.where(A, -EPS + C / qD, -EPS)
    vn = np.full(len(A), -EPS)
    q = np.where(A, qD, 0.0)
    g_gated = growth(vq, q, vn, 5 / qD + EPS)
    # uniform labeling at rate r on all events (cost 0 on agreement), PPI-style bound 5.1(2/r-1)
    vq_u = -EPS + C / r
    g_unif = growth(vq_u, np.full(len(A), r), vn, 5.1 * (2 / r - 1))
    return g_gated, g_unif, float(A.mean()), qD


if __name__ == "__main__":
    for r in (0.02, 0.05, 0.10, 0.20):
        out = np.array([seed_ratio(58400000 + k, r) for k in range(20)])
        gg, gu = out[:, 0].mean(), out[:, 1].mean()
        print(f"r={r:.2f} disagree={out[:,2].mean():.3f} qD={out[:,3].mean():.2f} "
              f"G_gated={gg:.5f} G_unif={gu:.5f} ratio(mean)={gg/gu:.1f}")
