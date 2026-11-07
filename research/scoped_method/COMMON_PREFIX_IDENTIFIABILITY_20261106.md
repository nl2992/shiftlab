# Common-prefix identifiability in the reversal headroom matrix

**Status:** deterministic design diagnostic, not a method experiment. It uses the registered synthetic generator only and does not open any real-data or locked source.

## Finding

The economically worthwhile `F3_reversal_1200` and unfavorable `F3_reversal_800` cells have the same policy-visible distribution through event 799. In `scripts/failure_atlas_v2_flq/regimes.py`, both use `p=.7` before event 800, disagreement rate `.2`, `rho=0`, delay 100, and `err_agree=.1`. They differ only in the later change point: the unfavorable cell switches to `p=.3` at event 800; the worthwhile cell switches at event 1200. The expected per-event challenger advantage in the shared prefix is `.2 * (2*.7 - 1) = +.08` in both.

I checked the generator directly with matched seeds 0–999: the complete two-model loss arrays were exactly equal on events 0–799 in all 1,000 pairs. Because the Failure Atlas replay exposes only model predictions (constructed as balanced labels XOR losses), the same-seed observable prediction histories also coincide through that prefix when the same replay RNG stream is used. The policy receives no regime label or covariate that signals which reversal horizon applies.

This yields an information constraint, not an impossibility theorem about all future methods: any policy adapted to the registered observation stream has the same decision distribution in both cells through event 799. The first potentially distinguishing labels arise only after the unfavorable change and its 100-event release delay. Thus a policy that promotes early enough to capture the worthwhile cell necessarily incurs the same early-promotion exposure in the unfavorable cell; rollback evidence arrives after reversal has begun. The target/adverse trade-off is built into the pair of regimes, rather than being solely a defect of the latest rollback detector.

## Consequence for the repair search

The existing candidate gates across both cells cannot be passed by adding a more aggressive pre-800 promotion trigger based only on the current stream. A new candidate would need a prospective observable signal that predicts persistence before event 800, or a materially different operating contract. Neither signal exists in the current loss-only Failure Atlas simulator. Repeatedly changing an e-SR/CUSUM threshold or start prior on these same cells would retune against an unobservable distinction and would not support a general claim.

This does not establish `NO_ECONOMIC_HEADROOM`: the oracle can exploit evaluator truth, and policies may still improve over the currently tested baseline under additional observable context. It does explain why the frozen safety/adverse-cell gate has not been met with the current information contract.

## Reproduction

```sh
PYTHONPATH=scripts/failure_atlas_v2_flq uv run python - <<'PY'
import numpy as np
from regimes import REGIMES
short = REGIMES['F3_reversal_800']
long = REGIMES['F3_reversal_1200']
for seed in range(1000):
    a = short.sample(np.random.default_rng(seed))
    b = long.sample(np.random.default_rng(seed))
    assert np.array_equal(a[:800], b[:800]), seed
print('1,000/1,000 paired prefixes equal')
PY
```

## Next testable path

Before another detector pilot, add or source an environment where model-pair predictions expose a pre-change context feature, then freeze a target rule that uses only that feature and the deployment-time filtration. The next smallest action is a read-only source audit for an existing chronological dataset with such a prospectively observable transition covariate and authentic model-pair predictions. If none is available, retain this as a benchmark/case study rather than claim a feasible repair from this synthetic pair.
