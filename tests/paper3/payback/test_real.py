import numpy as np

from shiftlab.paper3.payback.certificates import B0Window
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.real import net, run_episode, score_hold


def test_score_hold_and_truncation():
    z = np.array([0, 1, 1, -1, 1, 1, 0.0])  # T=6
    assert score_hold(z, 2, 3, 3.0) == (1 + -1 + 1 - 3.0, 3)
    g, hh = score_hold(z, 5, 4, 1.0)  # truncated to rounds 5,6
    assert hh == 2 and g == 0.0


def test_net_charges_labels_and_uncertified():
    assert net({"gross": 4.0, "labels": 10}, 0.05) == 3.5
    assert net({"gross": 0.0, "labels": 20}, 0.05) == -1.0


class Spy:
    def __init__(self, d):
        self.d, self.seen = d, []

    def start_batch(self, r, n):
        pass

    def observe(self, s, z, t):
        assert t == s + self.d  # released only at request time + delay
        self.seen.append((s, z, t))

    def lcb_sum(self, t, h):
        assert all(tt <= t for _, _, tt in self.seen)
        return 1e9 if t == 60 else -1e9


def test_certificate_never_sees_future():
    T, d = 200, 10
    z = np.concatenate([[0.0], np.where(np.arange(1, T + 1) % 2 == 0, 1.0, -1.0)])
    spy = Spy(d)
    r = run_episode(z, spy, h=50, d=d, B=150, n_plan=20)
    assert r["certified"] and r["t"] == 60 and all(s + d <= 60 for s, _, _ in spy.seen)
    assert r["gross"] == z[60:110].sum() - 3.0


def test_real_cert_runs():
    env = Envelope(0.002)
    z = np.concatenate([[0.0], np.ones(300)])
    r = run_episode(z, B0Window(env, 0.1, 20), h=50, d=10, n_plan=20)
    assert r["certified"] and r["gross"] == 47.0
