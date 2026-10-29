# Hard-budget delayed Online LLM Picker adaptation

**Date:** 2026-10-29. **Status:** comparator implementation with focused contract tests; no efficacy result.

## Source method and adaptation

Turrin et al., [Online LLM Picker](https://arxiv.org/abs/2610.01592), chooses query probabilities
from hypothetical committee-loss variance and posterior entropy, then updates an exponential-weights
posterior with importance-weighted losses. Its tested Section 4.3 protocol matches annotation
counts on average and releases labels immediately. This implementation is explicitly an adaptation,
not a faithful reproduction.

`src/shiftlab/dive/hard_budget_delayed_online_picker.py` implements the two-part query score for a
finite candidate set. It uses exact match/mismatch as the default response discrepancy, clips the
resulting propensity to `[0,1]`, reserves a request against the total budget immediately, and
updates cumulative importance-weighted losses only when a queried label is released after fixed
delay `d`. The propensity and posterior at request time are retained with the pending label; no
unqueried loss vector is passed to the controller. The delayed variance update uses the posterior
that was active when the prompt was queried.

Because the method can cease querying after the pathwise cap is consumed, its inverse-propensity
estimate describes only its pre-cap randomized acquisition process. It is a model-selection baseline,
not a time-uniform safety method. Comparisons that require false-promotion control must add a
separately specified, equally informed safety mechanism to every method or report this baseline only
on utility/query-efficiency endpoints. It must not be presented as providing the project's causal-null
risk guarantee.

## Contract checks

`tests/test_hard_budget_delayed_online_picker.py` verifies that (i) posterior loss estimates remain
unchanged before the release event, (ii) requests count against the cap while labels are pending,
(iii) the cap prevents later requests, (iv) labels release on the fixed event clock, and (v) identical
candidate outputs do not trigger a query. Run with:

```powershell
uv run pytest -q tests/test_hard_budget_delayed_online_picker.py
uv run ruff check src/shiftlab/dive/hard_budget_delayed_online_picker.py tests/test_hard_budget_delayed_online_picker.py
uv run ruff format --check src/shiftlab/dive/hard_budget_delayed_online_picker.py tests/test_hard_budget_delayed_online_picker.py
```

These checks establish implementation chronology and accounting only. No synthetic efficacy,
regret, safety calibration, or real-data claim has been evaluated. The adapted baseline does not
establish novelty for any future method.
