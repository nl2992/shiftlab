# Contract README: writing an external monitor adapter

Audience: an implementer who has not seen the evaluator. You need only
`src/shiftlab/contract/interface.py` (stdlib + numpy). Protocol: `P4_benchmark_value_gate.md`.

## What you implement

A class satisfying the `Monitor` protocol:

| Method | When the harness calls it | Your obligation |
|---|---|---|
| `reset(spec: TaskSpec)` | once, before the stream | clear all state; read `cost_bound`, `epsilon`, `alpha`, `horizon`, `label_budget`, `price_range` |
| `propensity(event) -> float` | every event, **before** the query coin | return `q` in `[0, 1]` using only past information and the public event |
| `observe(event, feedback)` | every event, after the coin | update your statistic; `feedback` is `None` if no label was bought |
| `log_e_value` (property) | after each `observe` | current log e-value for the eventwise null (conditional mean of `Z_t - epsilon` given the past is at most 0) |

The harness raises on a `propensity` outside `[0, 1]` (including NaN).

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
- It stops the stream when the remaining reserve falls below the largest price
  (`price_range[1]`), and declares an alarm at the first `log_e_value >= log(1/alpha)`.
- Oracle quantities (expected costs, onset times, scenario names) are never passed.

## Rules for your adapter

1. Import only the standard library, `numpy`, `scipy`, and `shiftlab.contract` (the interface
   module). Not `shiftlab.dive`, `shiftlab.decision_harm_experiment`, the evaluator, the
   harness, or the baselines. `shiftlab.contract.isolation.check_imports(path)` returns the list
   of violations; it must be empty. Relative and dynamic imports are flagged.
2. Your e-process must be valid for the eventwise null with your own propensity. If you
   test a weaker (running-average) null, disclose it.
3. `propensity` must not depend on the current outcome. It may depend on the current
   `PublicEvent` (including `remaining_budget` and `price`), but then bounds you derive from it
   must be handled per your filtration.
4. Keep all state in the object; `reset` must make runs independent.

## Minimal example: fixed-q Horvitz-Thompson monitor

```python
from __future__ import annotations

import numpy as np

from shiftlab.contract import Feedback, PublicEvent, TaskSpec


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
        # Ignores event.disagreement, so it pays for labels on agreements too.
        # A gated variant would return `self.q if event.disagreement else 0.0`
        # (keep the same bound C/q + epsilon, which holds for every event).
        return self.q

    def observe(self, event: PublicEvent, feedback: Feedback | None) -> None:
        if feedback is None:
            value = -self.spec.epsilon  # label not bought: HT term is 0
        else:
            value = feedback.paired_cost / feedback.propensity - self.spec.epsilon
        # E[value | past] = E[Z] - epsilon when Z is HT-unbiased, so the null gives <= 0.
        self.log_wealth += np.log1p(self.STAKES * value / self.bound)

    @property
    def log_e_value(self) -> float:
        peak = self.log_wealth.max()
        return float(peak + np.log(np.exp(self.log_wealth - peak).mean()))
```

Note: with a bought label the increment is `Z/q - epsilon` (`Z = 0` on an agreement); with no
label it is `-epsilon`. The coin is independent of `Z`, so `E[Z/q * 1{coin<q}] = E[Z]`. The bound `C/q + epsilon`
holds for every event.

## Running it

```python
import numpy as np
from shiftlab.contract import PublicEvent, TaskSpec
from shiftlab.contract.harness import run_monitor  # evaluator side

spec = TaskSpec(
    cost_bound=5.0, epsilon=0.1, alpha=0.05, horizon=n, label_budget=B, price_range=(0.5, 2.5)
)
events = [PublicEvent(i, x[i], int(dep[i]), int(ref[i]), False, 0.0, 0.0) for i in range(n)]
result = run_monitor(FixedQHT(), spec, events, paired_costs, uniforms, prices)
result.first_alarm, result.total_spend, result.log_e
```

`t`, `disagreement`, `price` and `remaining_budget` in the supplied events are overwritten by the
harness. In-repo baselines in `shiftlab.contract.baselines`: `GatedHTFixed` and `GatedHTPaced`
reproduce `replay_gated` log-e paths exactly on shared inputs (`tests/test_contract.py`);
`UniformHT` is the constant-q arm that pays for agreement labels.
