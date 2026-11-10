from shiftlab.paper3.payback import theory as th
from shiftlab.paper3.payback.envelope import Envelope


def _brute_worst_drop(v, J, hd, n):
    """max total decrease over n steps over all integer step sequences in the class (jumps >= hd apart)."""
    best = 0

    def rec(i, last_jump, tot):
        nonlocal best
        if i == n:
            best = max(best, tot)
            return
        rec(i + 1, last_jump, tot + v)  # drift step
        if last_jump is None or i - last_jump >= hd:
            rec(i + 1, i, tot + J)

    rec(0, None, 0)
    return best


def test_drop_matches_bruteforce():
    for v, J, hd in [(1, 1, 1), (1, 4, 3), (2, 7, 2), (1, 5, 6)]:
        env = Envelope(v, J, hd)
        for n in range(9):
            assert env.drop(n) == _brute_worst_drop(v, J, hd, n), (v, J, hd, n)


def test_irreducible_slack_pure_drift():
    env = Envelope(0.01)
    assert abs(env.irreducible_slack(5, 40) - 0.01 * (5 + 19.5)) < 1e-12


def test_bounds_ordering_and_tightness():
    base_rows = []
    for B, v, base in [(8, 0.0, 0.1), (14, 0.0, 0.1), (12, 0.01, 0.1), (12, 0.02, 0.15)]:
        a = b = 0.1
        lb = th.gamma_lb(B, v, base, a, b)
        npx = th.exact_np_gamma(B, v, base, a, b)
        ub, _n = th.gamma_ub(B, Envelope(v), a, b)
        assert lb <= npx + 1e-9 <= ub + 1e-9, (B, v, lb, npx, ub)
        assert ub / npx < 4.0
        base_rows.append((lb, npx, ub))
    # v=0: gamma ~ c/sqrt(B)
    g8 = th.gamma_lb(64, 0.0, 0.1, 0.05, 0.05)
    g4 = th.gamma_lb(256, 0.0, 0.1, 0.05, 0.05)
    assert 1.8 < g8 / g4 < 2.2


def test_budget_saturates_with_drift():
    a = b = 0.05
    v = 0.002
    g = lambda B: th.gamma_lb(B, v, 0.1, a, b)
    # beyond ~gamma/v labels nothing more helps (lower bound is flat in B)
    assert abs(g(2000) - g(4000)) < 1e-9 and g(100) > g(2000) + 1e-3
    assert th.saturation_budget(v, a, b) > 100
