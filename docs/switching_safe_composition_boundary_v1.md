# Safe-test composition: what it proves and what it leaves open

2026-10-28. **Status:** standard composition derivation and novelty boundary; not a candidate
algorithm or efficacy result.

## Contract

Let `Y_t` be a queried binary common-outcome label and let `Q_t` be chosen before `Y_t` is
generated. Write `F_(t-1)` for the complete event-time history. Under the one-sided global null,
assume `P(Y_t=1 | F_(t-1), Q_t=1) <= 1/2`. A query at event time s is observed at the start of
`s+d`, for fixed known `d>=1`; pending labels are not available. At most B queries may be issued
on any path.

For a specified Bernoulli alternative `p=1/2+epsilon`, `0<epsilon<=1/2`, define `lambda=2*epsilon`
and `G_t=1+lambda*Q_t*(2*Y_t-1)`. Then `G_t>=0` and under the null
`E[G_t | F_(t-1), Q_t]<=1`. Thus, for each fixed start tau,
`M_t^tau=product_(s=tau)^t G_s` (empty product one) is a nonnegative test supermartingale. For
predictable fixed weights `w_tau>=0`, `sum_tau w_tau=1`, the unknown-onset mixture
`M_t=sum_tau w_tau M_t^tau` is also a test supermartingale. Ville's inequality gives

`P_0(sup_(t<=T) M_t >= 1/alpha) <= alpha`.

Skipped queries insert factor one. The pathwise cap changes which factors can be observed but not
the supermartingale proof. With fixed delay and order-preserving release, visible wealth at the
start of round t is the event-time wealth through `t-d`; a visible crossing is contained in the
event-time crossing event, so the false-promotion bound is unchanged. This is the standard
e-detector construction in `switching_change_point_safe_baseline_v1.md`, specialized to paired
Bernoulli outcomes.

For repeated promotion episodes, allocate deterministic levels `alpha_e` with
`sum_e alpha_e<=alpha`. At each predictable episode start, reset wealth and use only queried
labels whose event times are at or after that start; do not reuse old wealth or pending labels.
Conditional Ville bounds each episode's false-promotion probability by `alpha_e`, and a union
bound controls any false promotion over the full null stream by alpha. A finite query cap may
leave a later episode without enough evidence; validity does not guarantee power.

## What the composition establishes

It establishes an anytime-valid false-promotion wrapper for any predictable query policy under
the declared conditional null, including a policy that observes previous released labels and
tracks a hard cap. It handles a late onset through the standard mixture over possible starts. A
fixed delay reduces the number of post-onset factors visible before a decision and adds the
already-proved delay loss; it does not invalidate the test. This broadly composes known
e-detectors and safe-test machinery with query/switch actions.

## What it does not establish

The multiplier `G_t` is selected for testing the null, not for net economic value. The e-process
does not say when a query is worth its price, when remaining labels should be reserved for a
possible reversal, whether switching recoups deployment cost, or how to bound cumulative regret
against a changing comparator. Under persistent iid benefit, a likelihood-ratio delay bound
applies to the test component; an exhausted hard budget truncates it. Under arbitrary reversal,
pre-reversal wealth is not evidence about current benefit and the next delayed labels cannot
prevent initial post-reversal losses. The method does not bound losses before rollback.

Therefore “budgeted acquisition + e-process + delayed action” is a valid composition pattern but
not a methodological contribution by itself. Any contribution must prove a new acquisition/action
coupling with a quantitative risk-regret advantage over this composition and the strongest
compatible cost-sensitive switching method. If it cannot clear that comparison under a defensible
persistence/dwell or drift assumption, revise or stop the hypothesis rather than expand the
benchmark suite.

For the one-switch persistent Bernoulli case, the exact threshold-and-hold economic accounting is
in [`switching_threshold_controller_decomposition_v1.md`](switching_threshold_controller_decomposition_v1.md):
net excess is the mean loss gap times the expected delayed crossing time, plus expected query
charges, minus the comparator's saved switch charge on no-cross paths. False-promotion control
does not bound any of those performance terms.
