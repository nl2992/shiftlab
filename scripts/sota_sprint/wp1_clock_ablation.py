"""Post hoc paired WP1 RMM label-clock vs elapsed-timestamp start-grid ablation.

The timestamp-indexed detector is limited to fresh UCI streams whose raw source retains timestamps.
It reuses the same RMM host, acquisition, alpha split, bet grid, and total number of starts; only the
start grid is spread across elapsed episode time instead of queried-label index. This is exploratory,
uses fixed episode endpoints, and does not establish a real-time guarantee.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen
from fam_e import HOSTS
from fresh_real import LOADERS, raw_zip
from registry import EXTRA
from suite import build_suite, stream_from_losses
from simulator import run_episode

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "rmm:gated_deployment+RMM"
WALLCLOCK = "rmm:gated_deployment+RMM_wallclock"
FRESH = ("metro", "beijing_pm25", "bike_hour", "appliances", "household_power")


class TimestampStartMixture:
    """Finite uniform mixture over starts evenly spaced in elapsed event timestamp."""
    def __init__(self, alpha, max_labels, cycle_start, episode_end, gap=10,
                 lambdas=(0.15, 0.3, 0.5)):
        self.alpha = float(alpha)
        self.n_starts = max(1, int(math.ceil(max_labels / gap)))
        self.starts = [int(cycle_start) + (int(episode_end) - int(cycle_start)) * j // self.n_starts
                       for j in range(self.n_starts)]
        self.lams = np.asarray(lambdas, dtype=float)
        self.products: list[np.ndarray] = []
        self.next_start = 0

    def update(self, x: int, sample_time: int) -> bool:
        while self.next_start < self.n_starts and self.starts[self.next_start] <= int(sample_time):
            self.products.append(np.ones(len(self.lams), dtype=float))
            self.next_start += 1
        factor = 1.0 + self.lams * int(x)
        for prod in self.products:
            prod *= factor
        stat = sum(float(p.mean()) for p in self.products) / self.n_starts
        return stat >= 1.0 / self.alpha


class TimestampIndexedRMM:
    """RMM wrapper whose detector starts use timestamp spacing; base host stays on event index."""
    def __init__(self, make_base, horizon, budget, alpha, *, rng, episode_end, name=""):
        from fam_b import RestartMixtureMonitor

        class _Wrapper(RestartMixtureMonitor):
            def __init__(self, *args, **kwargs):
                self.episode_end = int(episode_end)
                self.clock_start = None
                self.clock_now = None
                self.query_clock = {}
                self.deferred_feedback = []
                super().__init__(*args, **kwargs)
                self.det = None  # initialized when the first timestamped event arrives

            def _new_detector(self):
                if self.clock_start is None:
                    return None
                a = self.alpha_det / (2.0 ** self.n_promotions) if self.deployed == 0 else self.alpha_rb
                return TimestampStartMixture(a, self.B, self.clock_start, self.episode_end, self.gap)

            def observe(self, feedback):
                # The simulator delivers feedback before predict(event), so defer until that event
                # supplies the actual timestamp at which the label became available.
                self.deferred_feedback.extend(feedback)

            def _consume_feedback(self):
                fbs = self.deferred_feedback
                self.deferred_feedback = []
                to_base = []
                for fb in fbs:
                    d = int(fb.model_losses[0]) - int(fb.model_losses[1])
                    if fb.event_id in self.base_owned:
                        self.base_owned.discard(fb.event_id)
                        to_base.append(self.view.feedback(fb))
                    else:
                        self.own.discard(fb.event_id)
                    if d != 0:
                        self.queue[fb.event_id] = d
                if to_base:
                    self.base.observe(to_base)
                alarm = False
                while self.order and self.order[0] in self.queue:
                    event_id = self.order.pop(0)
                    d = self.queue.pop(event_id)
                    self.own.discard(event_id)
                    x = d if self.deployed == 0 else -d
                    clock = self.query_clock.pop(event_id)
                    if self.det.update(x, clock):
                        alarm = True
                        break
                if alarm:
                    self._switch()

            def predict(self, event):
                self.clock_now = int(event.context)
                if self.clock_start is None:
                    self.clock_start = self.clock_now
                    self.det = self._new_detector()
                self._consume_feedback()
                # Mirror RestartMixtureMonitor.predict, preserving event-clock semantics for host.
                self.t = event.t
                k = self.view.model(int(self.base.predict(self.view.event(event))))
                if self.override:
                    return self.deployed
                if k != self.deployed:
                    self.deployed = k
                    self.clock_start = self.clock_now
                    self.det = self._new_detector()
                    self.order, self.queue = [], {}
                    self.query_clock.clear()
                return self.deployed

            def request_labels(self, event, remaining_budget):
                dis = bool(event.model_predictions[0] != event.model_predictions[1])
                req = super().request_labels(event, remaining_budget)
                if req.requested and dis:
                    self.query_clock[event.t] = int(event.context)
                return req

            def _switch(self):
                # `clock_now` is the release event's timestamp; new starts may only accrue future
                # outcomes, never labels already released in this same observe batch.
                self.clock_start = int(self.clock_now)
                super()._switch()
                self.query_clock.clear()

        self.impl = _Wrapper(make_base, horizon, budget, alpha, rng=rng, name=name)

    def __getattr__(self, key):
        return getattr(self.impl, key)


def wallclock_factory(T, B, cs, cq, alpha, delay, r):
    base, seed_name = HOSTS["gated_deployment"]
    return TimestampIndexedRMM(base, T, B, alpha, rng=r(seed_name), episode_end=_CURRENT_END[0], name=WALLCLOCK)


_CURRENT_END = [0]  # assigned in the sequential episode runner before constructing the policy


@lru_cache(maxsize=None)
def timestamp_ns(name: str) -> np.ndarray:
    _, _, ts = LOADERS[name]()
    return ts.astype("int64").to_numpy()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _one(name, ep, seed, seed_base):
    zpath = ROOT / "data/sprint_fresh_losses" / f"{name}.npz"
    z = np.load(zpath)
    start = int(z["starts"][ep])
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    times = timestamp_ns(name)[start:start + len(losses)]
    if len(times) != len(losses) or np.any(np.diff(times) < 0):
        raise ValueError(f"timestamp alignment/order invalid for {name} episode {ep}")
    _CURRENT_END[0] = int(times[-1])
    extra = dict(EXTRA)
    extra[WALLCLOCK] = wallclock_factory
    seed_sub = seed_base + screen._h(name) % 1000
    run_ep = ep * 100_000 + seed
    policies = build_suite(len(losses), 200, 5.0, 0.05, 0.05, screen._delay(name), run_ep,
                           seed_sub, names=[BASELINE, WALLCLOCK], extra=extra)
    pred_rng = np.random.default_rng([seed_base, screen._h(name), ep, seed, 7])
    predictions, labels = stream_from_losses(losses, pred_rng)
    contexts = times.astype(np.int64)
    rows = []
    for pol in policies:
        res = run_episode(pol, model_predictions=predictions, labels=labels, contexts=contexts,
                          delay=screen._delay(name), budget=200, label_price=.05,
                          switch_cost=5.0, trace=True)
        if res.requested_labels > 200:
            raise AssertionError(f"budget exceeded by {pol.name}")
        rows.append({"regime": name, "episode": ep, "cluster": name, "seed": seed,
                     "policy": pol.name, "net": float(res.net_cost), "loss": float(res.prediction_loss),
                     "labels": int(res.requested_labels), "switches": int(res.deployment_switches),
                     "ever_promote": int(any(r["deployed_model"] == 1 for r in res.records)),
                     "elapsed_ns": int(times[-1] - times[0])})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed-base", type=int, default=2026110803)
    ap.add_argument("--out", type=Path, default=Path("outputs/sprint2/WP1/clock_ablation"))
    a = ap.parse_args(argv)
    out = a.out if a.out.is_absolute() else ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in FRESH:
        k = np.load(ROOT / "data/sprint_fresh_losses" / f"{name}.npz")["l0"].shape[0]
        for ep in range(k):
            for seed in range(a.seeds):
                rows.extend(_one(name, ep, seed, a.seed_base))
    rec_path = out / "records.jsonl"
    rec_path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    manifests = {name: {"loss_cache_sha256": sha256(ROOT / "data/sprint_fresh_losses" / f"{name}.npz"),
                        "raw_zip_sha256": sha256(raw_zip(name))} for name in FRESH}
    tracked_code = [Path(__file__), HERE / "fam_e.py", HERE / "fam_b.py", HERE / "screen.py",
                    HERE / "fresh_real.py", HERE / "analyze_wp1_clock_ablation.py",
                    ROOT / "scripts/failure_atlas_v2/restart_monitor.py",
                    ROOT / "scripts/failure_atlas_v2_flq/suite.py",
                    ROOT / "scripts/promising_directions/sota/simulator.py"]
    manifest = {"protocol": "post hoc paired WP1 label-clock vs elapsed-timestamp RMM ablation",
                "policy_names": [BASELINE, WALLCLOCK], "datasets": list(FRESH), "seeds": a.seeds,
                "seed_base": a.seed_base, "T": 2000, "B": 200, "cq": .05, "cs": 5.0,
                "alpha": .05, "units": "policy randomness seeds; episode is analysis unit",
                "timestamp_semantics": "raw source observation timestamps; labels retain registered event-delay in rows",
                "source_hashes": manifests,
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in tracked_code},
                "record_rows": len(rows)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {len(rows)} policy rows to {rec_path}")


if __name__ == "__main__":
    main()
