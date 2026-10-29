# Fixed-calendar ATC under a hard query cap and deterministic delay

**Status:** derived baseline adapter; not a new algorithm, safe-switching theorem, or efficacy
result. It transfers a tracking bound to the calendar-time scale while making the sampling and
delay penalties explicit.

## Contract

Let `X_t in [-1,1]` be independent, with piecewise-constant mean `mu_t`, at most `S` changes,
mean diameter at most `M`, and centered sub-Gaussian proxy `sigma^2`. A label queried at event `s`
is released at the start of `s+d`, for fixed integer `d>=1`. Labels are requested before their
outcomes, and the hard request cap counts pending labels.

For integers `2<=B<=T`, query the deterministic calendar

`q_1=1`, `q_B=T`, and `q_j=1+ceil((j-1)(T-1)/(B-1))` for `1<j<B`.

Its gaps are at most `L=ceil((T-1)/(B-1))`; it uses exactly `B` query rights. On the sampled
sequence `X_{q_1},...,X_{q_B}`, run ATC with its usual pre-observation prediction `mhat_j` based
on earlier sampled labels. At each calendar event, use the latest ATC prediction available from
released labels; set the initial estimate to zero before the first release. This baseline is
defined for tracking `mu_t`, not for promoting a model.

The sampled sequence remains independent, piecewise IID and sub-Gaussian. Write `S_q<=S` for
its number of sampled mean changes. Applying Gafni et al.'s Theorem 4.1 at horizon `B` gives

`R_ATC(B,S_q) <= C_V sigma^2(S_q+1+a)(1+log B)`
`                 + C_B sigma^2 S_q log(B/a)`
`                 + C_M M^2(a+S_q)`,

where `a in (0,1)` is ATC's restart false-alarm allocation parameter.

## Calendar-time guarantee

Let `mhat(t)` be the latest released-label estimate. Then

`E[sum_{t=1}^T (mhat(t)-mu_t)^2]`
` <= d + 2 L R_ATC(B,S_q) + 2 M^2 S (L+d).`                 (1)

The first term bounds the `d` calendar events before the first queried label can arrive, using
`|mu_t|<=1`. For `j>=2`, on the interval `[q_{j-1}+d, q_j+d)` the learner has seen exactly
the first `j-1` queried outcomes and uses `mhat_j`. Compare it to the sampled target
`mu_{q_j}` using
`(mhat_j-mu_t)^2 <= 2(mhat_j-mu_{q_j})^2 + 2(mu_{q_j}-mu_t)^2`.
The interval has at most `L` events, so the first terms sum to at most `2L R_ATC(B,S_q)`.

The second term is nonzero only when a regime change lies between the calendar event `t` and
the next sampled event `q_j`. For any one change this can occur on at most `L` events before
the first sampled point on the new side and at most `d` events after a sampled point but before
its label releases. There are at most `S` changes and the mean diameter is `M`; hence the total
staleness contribution is at most `2M^2 S(L+d)`. This proves (1), including changes that occur
between queried events or whose labels remain pending at the horizon.

For bounded paired-loss differences, `mu_t` is the conditional challenger benefit. The
sign-action rule `A_t=1{mhat(t)>0}` has expected gross decision regret against the clairvoyant
per-event sign action at most

`sqrt(T * [d + 2 L R_ATC(B,S_q) + 2 M^2 S(L+d)])`,

because a sign mistake implies `|mu_t|<=|mhat(t)-mu_t|`, followed by Cauchy–Schwarz. This is
only a gross per-event decision bound. It does not bound the learner's number of switches,
query fees, regret to a comparator charging a fixed switch budget, or any false-promotion event.
ATC's `a` controls false detector restarts in its tracking proof; it is not ShiftLab's causal-null
promotion level `alpha`.

## What this baseline does and does not establish

Equation (1) is a direct adapter bound, not an independently novel result. It provides an explicit
comparison point for the benefit-estimation component under the same hard `B` and delay `d`.
When `B` is small or `d` is large, the calendar and staleness terms can dominate; the bound is
then vacuous for method selection. ATC has no causal-null gate, and bolting on a standard e-process
would establish safety only for the e-process's declared test-epoch null, not a new current-value
or switching-regret theorem. A full safe switching baseline still needs an explicit deployment
rule and risk accounting across repeated promotions.

Reproduce the source scope with `switching_gafni_theorem_audit_v1.md`. No simulation or data
evaluation is authorized or claimed by this analytic adapter.
