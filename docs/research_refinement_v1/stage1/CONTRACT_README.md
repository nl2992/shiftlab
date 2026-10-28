# Contract README: writing an external monitor adapter

Audience: an implementer who has not seen the evaluator. You receive an **implementation packet**
(built by `shiftlab.contract.sandbox.build_packet`): a directory with `interface.py` (stdlib +
numpy), this README, the P4 protocol, and your adapter file. You do not receive the repository.
Protocol: `P4_benchmark_value_gate.md`.

## What you implement

An adapter file that defines `build_monitor()` returning an object with the `Monitor` interface,
importing the contract as `from interface import ...`:

| Method | When the harness calls it | Your obligation |
|---|---|---|
| `reset(spec: TaskSpec)` | once, before the stream | clear all state; read `cost_bound`, `epsilon`, `alpha`, `horizon`, `label_budget`, `price_range` |
| `propensity(event) -> float` | every event, **before** the query coin | return `q` in `[0, 1]` using only past information and the public event |
| `observe(event, feedback)` | every event, after the coin | update your statistic; `feedback` is `None` if no label was bought |
| `log_e_value` (property) | after each `observe` | current log e-value for the eventwise null (conditional mean of `Z_t - epsilon` given the past is at most 0) |

The harness raises on a `propensity` outside `[0, 1]` (including NaN) and on a non-finite
`log_e_value`.

## What the harness does

- It draws the query coin itself from a registered stream. Your code never sees the coin.
- It queries any event, agreement or disagreement, whenever `coin < q`.
- It charges `event.price` per bought label and refuses a query that would overdraw the reserve.
  A refused query is recorded and you get `feedback=None`.
- There is no free feedback. Feedback is passed only after the coin, for bought labels:
  `Feedback(t, paired_cost=Z_t, propensity=q)` with the `q` you returned.
- On agreements the paired cost is exactly zero, so a queried agreement delivers
  `paired_cost=0.0`, but it is still charged. A monitor that uses `event.disagreement` can return
  `q = 0.0` on agreements and never pay for them (the gated baselines do); one that ignores the
  flag pays for agreement labels (`UniformHT`). `feedback is None` means "label not bought".
- Reserve stop (locked, one default): the stream stops before an event when the remaining reserve
  is below `price_range[1]`. The rule is recorded in `HarnessResult.reserve_stop_rule`.
- It declares an alarm at the first `log_e_value >= log(1/alpha)` and keeps running.
- Oracle quantities (expected costs, onset times, scenario names) are never passed.

## Rules for your adapter

1. Import only the standard library, `numpy`, `scipy` and `interface`. The adapter runs in an
   isolated subprocess (`python -I`, working directory = the packet, stripped environment,
   `shiftlab` blocked, and an audit-hook guard denying file access outside the packet, subprocess,
   sockets and ctypes; stdlib, numpy and scipy remain readable); events and feedback arrive as
   JSON, so state must live in your object. Do not use `gc`, `inspect`, `ctypes`, frame, closure,
   `__code__`, `__globals__` or `__builtins__` access; the lint rejects them and the guard denies
   them. Threat model: a non-adversarial implementer, adapter source reviewed and hashed by the
   lead before the run, plus this in-process guard. It is not an OS sandbox, so the procedural
   packet-only rule still applies.
   `shiftlab.contract.isolation.check_imports(path)` is a lint only. It does not establish
   isolation.
2. Your e-process must be valid for the eventwise null with your own propensity. If you test a
   weaker (running-average) null, disclose it.
3. **Propensity and bound rule.** If `propensity(event)` depends on the *current* event (its
   covariates, price, disagreement flag or remaining budget), then either
   (a) use a bound for the increment that is **global**, valid for the full propensity range
   (for HT: `C/q_min + epsilon`), or
   (b) establish and state the stronger null that conditions on the current context
   (`E[Z_t - epsilon | F_{t-1}, current event] <= 0`) and use the event-specific bound
   `C/q_t + epsilon` under it.
   A bound computed from `q_t` is predictable only with respect to the filtration that includes
   the current context. Under a null conditioned on the past alone, `E[value/bound | past]`
   need not be `<= 0` when `bound` varies with the current context. Predictable-only
   propensities (functions of past observations and the clock) may use `C/q_t + epsilon`.
4. Your submission must include an explicit written argument for the HT weighting, the null
   and the bound (see P4 section 2), and the paper-faithful numerical fixture.
5. Keep all state in the object; `reset` must make runs independent.

## Minimal example: fixed-q Horvitz-Thompson monitor

```python
from __future__ import annotations

import numpy as np

from interface import Feedback, PublicEvent, TaskSpec


class FixedQHT:
    """Fixed propensity q; HT increment; mixture of fixed bets (bounded-mean e-process)."""

    STAKES = np.array([0.05, 0.1, 0.2, 0.4, 0.8])

    def __init__(self, q: float = 0.3) -> None:
        self.q = q

    def reset(self, spec: TaskSpec) -> None:
        self.spec = spec
        self.bound = spec.cost_bound / self.q + spec.epsilon
        self.log_wealth = np.zeros(len(self.STAKES))

    def propensity(self, event: PublicEvent) -> float:
        # q is constant, so the global bound C/q + epsilon is valid. Ignoring
        # event.disagreement means this monitor pays for labels on agreements too.
        return self.q

    def observe(self, event: PublicEvent, feedback: Feedback | None) -> None:
        if feedback is None:
            value = -self.spec.epsilon  # label not bought: HT term is 0
        else:
            value = feedback.paired_cost / feedback.propensity - self.spec.epsilon
        self.log_wealth += np.log1p(self.STAKES * value / self.bound)

    @property
    def log_e_value(self) -> float:
        peak = self.log_wealth.max()
        return float(peak + np.log(np.exp(self.log_wealth - peak).mean()))


def build_monitor() -> FixedQHT:
    return FixedQHT()
```

With a bought label the increment is `Z/q - epsilon` (`Z = 0` on an agreement); with no label it is
`-epsilon`. The coin is independent of `Z`, so `E[Z/q * 1{coin<q}] = E[Z]`, and the bound
`C/q + epsilon` holds for every event. This example is a plumbing illustration; it is not an
acceptable gate submission (see P4 section 2).

## Running it (evaluator side)

```python
from shiftlab.contract import PublicEvent, TaskSpec
from shiftlab.contract.sandbox import SandboxedMonitor
from shiftlab.contract.harness import run_monitor

spec = TaskSpec(
    cost_bound=5.0, epsilon=0.1, alpha=0.05, horizon=n, label_budget=B, price_range=(0.5, 2.5)
)
events = [PublicEvent(i, x[i], int(dep[i]), int(ref[i]), False, 0.0, 0.0) for i in range(n)]
with SandboxedMonitor("adapter.py") as monitor:  # isolated subprocess
    result = run_monitor(monitor, spec, events, paired_costs, uniforms, prices)
result.first_alarm, result.total_spend, result.log_e, result.reserve_stop_rule
```

`t`, `disagreement`, `price` and `remaining_budget` in the supplied events are overwritten by the
harness. In-repo baselines in `shiftlab.contract.baselines`: `GatedHTFixed` and `GatedHTPaced`
reproduce `replay_gated` log-e paths exactly on shared inputs, and `UniformHT(q=r)` (q passed
explicitly) reproduces E2's `replay_uniform("uniform_ht")` exactly (`tests/test_contract.py`).
`UniformHT` is the constant-q arm that pays for agreement labels.
