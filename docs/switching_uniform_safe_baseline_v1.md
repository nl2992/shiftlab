# Uniform-query all-onset safe-switch baseline calculation

2026-10-28. **Status:** analytical comparator evaluation; no new method or efficacy result.

## Baseline and finite-horizon bound

Use the audited Shin–Ramdas–Rinaldo all-onset likelihood-ratio mixture with weights
`w_tau=1/T`. Before outcomes, fix a query schedule of at most `B` distinct event times, evenly
spaced over `1,...,T-d`, so every issued label is available by the horizon. For Bernoulli null
`1/2` versus post-change alternative `1/2+epsilon`, each queried post-onset label contributes

`X = Y log(1+2 epsilon) + (1-Y) log(1-2 epsilon)`

to the onset-`nu` component. Its mean is
`kappa=KL(Ber(1/2+epsilon)||Ber(1/2))`; its range width is
`R=log((1+2 epsilon)/(1-2 epsilon))`. The mixture promotes once its visible value reaches
`1/alpha`, and then holds policy 1.

If `m_t` scheduled post-onset labels have arrived by the action at time `t`, the onset component
forces promotion by that time whenever its log likelihood is at least
`a=log(T/alpha)`. Hoeffding therefore gives

`P(A_t=0) <= min(1, exp(-2 (m_t*kappa-a)^2/(m_t*R^2)))`

when `m_t*kappa>a`, and the bound 1 otherwise. Against the oracle that stays at 0 before `nu`
and switches once at `nu`, with zero pre-change paired gap and post-change gap `2 epsilon`, the
expected gross decision regret is at most `2 epsilon * sum_{t=nu}^T P(A_t=0)` under this bound.
The learner's one deployment switch costs either zero or `k`, while the oracle pays `k`, so this
term cannot increase net excess; query cost adds `c` times the issued query count. Under the
conditional Bernoulli null, the predictable fixed query schedule and ordered delay preserve the
all-onset mixture's global false-promotion probability at most `alpha`.

The onset-component check alone is insufficient to show that the *mixture* cannot cross:
components starting before `nu` also use pre-change labels. For the entire mixture, every queried
label factor is maximized at `Y=1` and exceeds one. Thus the exact pathwise maximum over all label
sequences and all visible times is attained at the horizon with every queried label positive:

`M_max = (1/T) * sum_(tau=1)^T (1+2 epsilon)^(# {s in schedule : s>=tau})`.

If this maximum is below `1/alpha`, no component combination can cross on any path, including
paths with favorable pre-change labels. The policy then never promotes and incurs exactly the full
post-change gross regret `2 epsilon (T-nu+1)`.

## Calculation

Reproduce with:

`python scripts/evaluate_switching_uniform_safe_baseline.py`

The registered cell is `T=120`, `nu=61`, `B=20`, `epsilon=.10`, `alpha=.05`, with delays
`d in {1,5,20}`. The crossing threshold is `1/alpha=20`. The exact maximum of the *full mixture*
over all label paths is `11.1996`, `10.8952`, and `9.5011`, respectively. This includes evidence
from components starting before the true onset, closing the component-only argument gap.
Therefore this fixed uniform-query/all-onset-mixture composition cannot promote on any path in
these cells; its gross regret is exactly 12, the full available post-change gap. This exposes a
poor acquisition allocation for this setting, but is not a separation from optimized mixtures,
calibrated randomized tests, controlled sensing, or constrained planning. The uniform onset prior
and query schedule are comparison choices, not optimality claims.

The concentration bound is deterministic; the no-crossing and gross-regret result is exact and
pathwise for the registered cells. This is not a Monte Carlo experiment, confirmation study,
candidate-method result, or novelty evidence. G1 remains open; use a stronger equally equipped
baseline before any efficacy claim.
