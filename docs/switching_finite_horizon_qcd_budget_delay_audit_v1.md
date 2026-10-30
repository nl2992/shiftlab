# Finite-horizon QCD and the delayed hard-cap boundary

**Date:** 2026-10-29. **Status:** source-level comparator audit and supporting lower bound;
not a new detection algorithm or novelty claim.

## Primary-source result

Huang and Veeravalli, [*Finite-Horizon Quickest Change Detection Balancing Latency with False
Alarm Probability*](https://arxiv.org/abs/2511.12803), arXiv:2511.12803 (2025). The full primary
HTML source was inspected for its model, definitions, Theorems 1–3, and proof arguments in
Appendices A, B and D.

The paper studies independent observations with one unknown change from `f0` to `f1`. It constrains
the probability of any false alarm by time `T` and minimizes a high-probability latency quantile,
requiring `P_nu(tau >= nu + ell) <= delta_D` for every change point in its range. For known
distributions, its time-varying-threshold CuSum and Shiryaev–Roberts tests control finite-horizon
false alarm probability and have `O(log T)` latency; the paper also gives an asymptotic latency
lower bound. For unknown Gaussian means with a sub-Gaussian model, it analyzes generalized CuSum
and Shiryaev–Roberts tests. Its lower-bound information constant is
`log E_f1[f1(X)/f0(X)]`, not `KL(f1 || f0)`.

This occupies finite-horizon false-alarm/latency tradeoffs for fully observed, immediate-feedback
change detection. The theorem does not cover adaptive selective labels under a total pathwise cap,
pending labels and release delay, query or switching charges, a distinct economic switching
objective, or repeated reversible promotion. Therefore latency quantiles and familywise false-alarm
control alone are not a novelty delta. It is a required detector baseline wherever a persistent
one-change subproblem is compared.

## Delayed hard-cap information lower bound

Consider a finite horizon `T`, one queried observation at most per event, fixed release delay
`d >= 1` (a label from event `s` is available at the start of `s+d`), and a pathwise request cap
`B`, counting pending requests. There is no informative unqueried covariate. Under `P_infinity`,
observations are IID from `f0`; under `P_nu`, they are IID from `f0` before `nu` and from `f1`
starting at `nu`. Assume `0 < KL(f1 || f0) < infinity`. The learner may randomize and choose
queries and an alarm using only its observable history. Suppose

```text
P_infinity(tau <= T) <= delta_F
P_nu(tau >= nu + ell) <= delta_D
```

for every onset whose full `ell`-event window lies in the horizon. Let
`M = floor(T / ell) >= 1`, and assume `1 - delta_F - delta_D > delta_F/M`. Then necessarily

```text
min(B, max(0, ell-d)) * KL(f1 || f0)
    >= kl_Ber(1-delta_F-delta_D || delta_F/M),
```

where `kl_Ber` is binary relative entropy. In particular, if the right side divided by
`KL(f1 || f0)` exceeds `B`, the requested false-alarm and latency levels are infeasible for every
adaptive acquisition rule. If feasible, the latency must also satisfy
`ell >= d + ceil(kl_Ber(...)/KL(f1 || f0))`.

**Proof.** Partition the horizon into `M` disjoint windows of length `ell`, starting at
`nu_j = 1 + j*ell`. Since the total null alarm probability is at most `delta_F`, at least one
window has `P_infinity(nu_j <= tau < nu_j+ell) <= delta_F/M`. Fix this onset. Under `P_nu`,
the probability of an alarm before `nu_j` equals its null probability and is at most `delta_F`.
The latency condition therefore implies
`P_nu(nu_j <= tau < nu_j+ell) >= 1-delta_F-delta_D`.

Let `O` be the learner's transcript through the decision at `nu_j+ell-1`. Query and action
kernels contribute no KL because they are the same functions of the observed history under both
laws. At most `max(0,ell-d)` post-change queried labels can have been released by that decision,
and at most `B` can have been requested on any path. The adaptive chain rule gives
`KL(P_nu(O) || P_infinity(O)) <= min(B,max(0,ell-d))*KL(f1||f0)`. Apply data processing to the
window-alarm indicator. Its alternative probability is at least `1-delta_F-delta_D`; its null
probability is at most `delta_F/M`. Monotonicity of binary KL in this region proves the claim.
QED.

This is the standard adaptive KL/data-processing argument plus a disjoint-window packing step,
specialized to a delayed hard cap. It is supporting theory, not a new information inequality. It
does not bound economic regret, switching costs, or current benefit after an unobserved reversal.

## Frozen feasibility check

For `T=120`, `B=20`, `d=1`, `P0=Ber(1/2)`, `P1=Ber(0.6)`, `delta_F=0.05`, and
`delta_D=0.10`, the smallest right-hand requirement over `M=1,...,120` occurs at `M=1`:

```text
kl_Ber(0.85 || 0.05) = 2.1313573389
KL(Ber(0.6) || Ber(0.5)) = 0.0201355136
required informative labels >= ceil(105.8507) = 106
```

The hard cap is only 20, so no rule can meet a 90%-within-`ell` detection guarantee at 5%
finite-horizon false alarm in this weak-signal cell, even with the entire horizon. This does not
say that expected decision regret cannot improve, or that stronger-signal cells are infeasible.
It says a high-probability detector-latency endpoint would be an impossible target for this
registered parameter cell. The existing expected-regret lower bounds remain the relevant primary
metric for algorithm search.

## Research decision

Add Huang–Veeravalli TVT-CuSum/TVT-SR (and the generalized tests when assumptions match) to the
matched detector baselines. Do not describe the finite-horizon false-alarm/latency formulation as
open. Use the capped-delay lower bound to screen latency claims and exclude the weak-signal cell
from any high-probability detection target. G1 remains open only for an acquisition-and-reversible-
switching method with a net-utility or regret theorem beyond this detector baseline, hard-budget
delayed-learning methods, and the exact constrained oracle. G2–G5 remain held.
