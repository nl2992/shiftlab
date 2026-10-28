"""Tests for the public monitor contract, harness, baselines and isolation check."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.special import ndtr

from shiftlab.contract import Feedback, PublicEvent, TaskSpec, interface
from shiftlab.contract.baselines import GatedHTFixed, GatedHTPaced, UniformHT
from shiftlab.contract.harness import run_monitor
from shiftlab.contract.isolation import check_imports, check_source
from shiftlab.dive.gated_monitor_comparison import DisagreementPacer, replay_gated

CONTRACT_DIR = Path(interface.__file__).parent


def _synthetic_stream(seed: int, n: int = 600, shift: float = 3.0):
    """Inputs in the shape ``replay_gated`` takes; harmful costs after the midpoint."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n + 800, 4))
    active = rng.random(n + 800) < np.where(np.arange(n + 800) < 800 + n // 2, 0.15, 0.4)
    tariffs = rng.uniform(0.5, 2.5, size=n + 800)
    mean = np.where(np.arange(n + 800) < 800 + n // 2, -0.5, shift)
    paired = np.clip(rng.normal(mean, 1.0), -5, 5) * active
    uniforms = rng.random(n)
    return x, paired, active, tariffs, uniforms


def _real_stream(scenario: str, seed: int):
    """Same input construction as ``comparison_seed`` (S3 generation path), CPU only."""
    from shiftlab.decision_harm_experiment import (
        SCENARIOS,
        ExperimentConfig,
        _generate,
        _source_action,
    )
    from shiftlab.dive.experiment import _binary_cost, _synthetic_label_costs

    sc = next(s for s in SCENARIOS if s.name == scenario)
    base = ExperimentConfig(
        n=3200,
        d=16,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=800,
        window=64,
        stride=32,
        alpha=0.05,
        eprocess_epsilon=0.1,
        seed_offset=seed,
        change_fraction=0.5,
        device="cpu",
    )
    _, frame, _, _ = _generate(sc, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if sc.harmful_adaptation:
        deployed[1600:] = 1
    reference = _source_action(x, sc)
    active = deployed != reference
    tariffs = _synthetic_label_costs(x)
    paired = _binary_cost(deployed, y, sc.fn_cost, sc.fp_cost) - _binary_cost(
        reference, y, sc.fn_cost, sc.fp_cost
    )
    uniforms = np.random.default_rng(seed + 9_173).random(3200)
    return x, paired, active, tariffs, uniforms[:2400], deployed, reference


def _run_both(
    arm, monitor_cls, x, paired, active, tariffs, uniforms, rate, deployed=None, ref=None
):
    start = 800
    kwargs = {
        "validation_disagreement": active[400:800],
        "validation_tariffs": tariffs[400:800],
        "budget_rate": rate,
    }
    replay = replay_gated(
        arm=arm,
        x=x[start:],
        paired_cost=paired[start:],
        disagreement=active[start:],
        tariffs=tariffs[start:],
        uniforms=uniforms,
        **kwargs,
    )
    n = len(uniforms)
    pacer = DisagreementPacer(kwargs["validation_disagreement"], kwargs["validation_tariffs"], rate)
    spec = TaskSpec(5.0, 0.1, 0.05, n, pacer.target * n, (0.5, 2.5))
    dep = active[start:].astype(int) if deployed is None else deployed[start:]
    ref_a = np.zeros(n, dtype=int) if ref is None else ref[start:]
    events = [
        PublicEvent(i, x[start + i], int(dep[i]), int(ref_a[i]), False, 0.0, 0.0) for i in range(n)
    ]
    result = run_monitor(
        monitor_cls(**kwargs), spec, events, paired[start:], uniforms, tariffs[start:]
    )
    return replay, result


@pytest.mark.parametrize(
    ("arm", "cls"), [("gated_ht_fixed", GatedHTFixed), ("gated_ht_paced", GatedHTPaced)]
)
@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("rate", [0.05, 0.2])
def test_parity_with_replay_gated_synthetic(arm, cls, seed, rate):
    x, paired, active, tariffs, uniforms = _synthetic_stream(seed)
    replay, result = _run_both(arm, cls, x, paired, active, tariffs, uniforms, rate)
    assert result.processed == len(replay.log_e)
    np.testing.assert_array_equal(result.log_e, replay.log_e)
    # The contract returns q only on disagreements (0.0 on agreements); replay logs the latent q.
    dis = active[800:][: result.processed]
    np.testing.assert_array_equal(result.propensities[dis], replay.propensities[dis])
    assert np.all(result.propensities[~dis] == 0.0)
    np.testing.assert_array_equal(result.queried, replay.queried)
    assert result.first_alarm == replay.first_alarm
    assert result.total_spend == replay.dollars
    assert result.budget == replay.budget
    assert not result.refused.any()


@pytest.mark.parametrize(
    "arm_cls", [("gated_ht_fixed", GatedHTFixed), ("gated_ht_paced", GatedHTPaced)]
)
def test_parity_on_real_s3_stream(arm_cls):
    arm, cls = arm_cls
    x, paired, active, tariffs, uniforms, dep, ref = _real_stream("boundary_local_harm", 123)
    replay, result = _run_both(arm, cls, x, paired, active, tariffs, uniforms, 0.2, dep, ref)
    np.testing.assert_array_equal(result.log_e, replay.log_e)
    assert result.first_alarm == replay.first_alarm
    assert result.total_spend == replay.dollars
    assert result.queried.sum() > 0


def test_reserve_stop_matches_replay_and_can_be_disabled():
    """replay_gated stops when budget - spent < 2.5; the harness matches by default."""
    x, paired, active, tariffs, uniforms = _synthetic_stream(5, n=1500)
    replay, result = _run_both(
        "gated_ht_fixed", GatedHTFixed, x, paired, active, tariffs, uniforms, 0.02
    )
    assert replay.log_e.shape[0] < 1500  # reserve actually binds in this configuration
    assert result.stopped_early and result.processed == replay.log_e.shape[0]


class _SpyMonitor:
    """Always queries; records what the harness hands over."""

    def __init__(self, q: float = 1.0):
        self.q = q
        self.calls: list[tuple[PublicEvent, Feedback | None]] = []
        self.order: list[str] = []

    def reset(self, spec):
        self.spec = spec

    def propensity(self, event):
        self.order.append("propensity")
        return self.q

    def observe(self, event, feedback):
        self.order.append("observe")
        self.calls.append((event, feedback))

    @property
    def log_e_value(self):
        return 0.0


def _simple_events(n, disagree_every=2):
    return [
        PublicEvent(i, np.zeros(2), int(i % disagree_every == 0), 0, False, 0.0, 0.0)
        for i in range(n)
    ]


def _spec(n, budget=1000.0):
    return TaskSpec(5.0, 0.1, 0.05, n, budget, (0.5, 2.5))


def test_feedback_only_for_queried_events_and_agreements_are_charged():
    n = 200
    rng = np.random.default_rng(0)
    coins = rng.random(n)
    costs = rng.uniform(-1, 1, n)
    prices = rng.uniform(0.5, 2.5, n)
    spy = _SpyMonitor(q=0.5)
    result = run_monitor(spy, _spec(n), _simple_events(n), costs, coins, prices)
    for i, (event, feedback) in enumerate(spy.calls):
        expected = coins[i] < 0.5
        assert (feedback is not None) == expected
        assert result.queried[i] == expected
        if expected:
            want = costs[i] if event.disagreement else 0.0
            assert feedback == Feedback(i, want, 0.5)
            assert result.spend[i] == prices[i]
        else:
            assert result.spend[i] == 0.0
    assert any(fb is not None and not ev.disagreement for ev, fb in spy.calls)
    assert spy.order[:2] == ["propensity", "observe"]
    assert result.total_spend == pytest.approx(prices[result.queried].sum())


def test_unqueried_costs_are_never_read():
    n = 100
    costs = np.full(n, np.nan)  # NaN would raise if read for an unqueried event
    spy = _SpyMonitor(q=0.0)
    run_monitor(spy, _spec(n), _simple_events(n), costs, np.full(n, 0.5), np.ones(n))
    assert all(fb is None for ev, fb in spy.calls if ev.disagreement)


def test_refused_query_is_recorded_and_unqueried():
    n = 10
    spy = _SpyMonitor(q=1.0)
    result = run_monitor(
        spy,
        _spec(n, budget=3.0),
        _simple_events(n, 1),
        np.zeros(n),
        np.zeros(n),
        np.full(n, 2.0),
        stop_when_reserve_below_max_price=False,
    )
    assert result.queried[0] and result.refused[1:].all()
    assert result.total_spend == 2.0 and not result.queried[1:].any()
    assert all(fb is None for ev, fb in spy.calls[1:])


@pytest.mark.parametrize("bad", [-0.1, 1.5, float("nan"), float("inf")])
def test_out_of_range_propensity_rejected(bad):
    n = 5
    with pytest.raises(ValueError, match="outside"):
        run_monitor(
            _SpyMonitor(q=bad), _spec(n), _simple_events(n), np.zeros(n), np.zeros(n), np.ones(n)
        )


def test_uniform_ht_runs_through_harness():
    n = 300
    x, paired, active, tariffs, uniforms = _synthetic_stream(7, n=n)
    spec = TaskSpec(5.0, 0.1, 0.05, n, 400.0, (0.5, 2.5))
    events = [PublicEvent(i, x[i], int(active[800 + i]), 0, False, 0.0, 0.0) for i in range(n)]
    result = run_monitor(UniformHT(q=0.5), spec, events, paired[800:], uniforms, tariffs[800:])
    assert result.processed > 0 and np.all(result.propensities == 0.5)


def test_isolation_flags_forbidden_imports_and_accepts_allowed():
    assert check_source("import shiftlab.dive\n")
    assert check_source("from shiftlab.dive.eprocess import PredictableBoundMeanEProcess\n")
    assert check_source("from shiftlab.contract.harness import run_monitor\n")
    assert check_source("from shiftlab.contract import baselines\n")
    assert check_source("import shiftlab.decision_harm_experiment\n")
    assert check_source("import torch\n")
    assert check_source("from . import sibling\n")
    assert check_source("import importlib\nimportlib.import_module('shiftlab.dive')\n")
    allowed = (
        "from __future__ import annotations\nimport math\nimport numpy as np\n"
        "from scipy.special import logsumexp\n"
        "from shiftlab.contract import TaskSpec\n"
        "from shiftlab.contract.interface import Feedback, Monitor\n"
    )
    assert check_source(allowed) == []


def test_isolation_on_files(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import shiftlab.dive\n", encoding="utf-8")
    good = tmp_path / "good.py"
    good.write_text("import numpy\nfrom shiftlab.contract.interface import TaskSpec\n")
    assert check_imports(bad) and check_imports(good) == []


def test_interface_imports_nothing_outside_contract():
    assert check_imports(CONTRACT_DIR / "interface.py") == []
    for name in ("interface.py", "__init__.py"):
        tree = ast.parse((CONTRACT_DIR / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("shiftlab") for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                assert not (node.module or "").startswith("shiftlab")
    # __init__ re-exports interface only (relative import of one sibling).
    init = ast.parse((CONTRACT_DIR / "__init__.py").read_text(encoding="utf-8"))
    relative = [n.module for n in ast.walk(init) if isinstance(n, ast.ImportFrom) and n.level]
    assert relative == ["interface"]


def test_importing_contract_does_not_load_evaluator():
    code = (
        "import sys, shiftlab.contract;"
        "bad=[m for m in sys.modules if m.startswith(('shiftlab.dive','shiftlab.decision_harm',"
        "'shiftlab.contract.harness','shiftlab.contract.baselines'))];"
        "assert not bad, bad"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_uniform_ht_pays_for_agreements_and_covers_fewer_disagreements_than_gated():
    n = 1000
    x, paired, active, tariffs, uniforms = _synthetic_stream(11, n=n)
    start = 800
    pacer = DisagreementPacer(active[400:800], tariffs[400:800], 0.2)
    spec = TaskSpec(5.0, 0.1, 0.05, n, pacer.target * n, (0.5, 2.5))
    dis = active[start:]
    events = [PublicEvent(i, x[start + i], int(dis[i]), 0, False, 0.0, 0.0) for i in range(n)]
    args = (events, paired[start:], uniforms, tariffs[start:])
    uniform = run_monitor(UniformHT(), spec, *args)
    gated = run_monitor(
        GatedHTFixed(
            validation_disagreement=active[400:800],
            validation_tariffs=tariffs[400:800],
            budget_rate=0.2,
        ),
        spec,
        *args,
    )
    d_u = dis[: uniform.processed]
    d_g = dis[: gated.processed]
    assert uniform.spend[~d_u].sum() > 0  # pays for agreement labels
    assert gated.spend[~d_g].sum() == 0  # gated never pays for agreements
    assert uniform.queried[d_u].sum() < gated.queried[d_g].sum()
    assert np.all(uniform.propensities == uniform.propensities[0])
