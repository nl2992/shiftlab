# Unknown-onset mixture information lower bound

2026-10-28. **Status:** registered derivation/evaluation; standard information inequalities,
not a novelty claim. This tightens the unknown-onset comparison by using the shared global
false-promotion event jointly across onset hypotheses.

## Frozen contract and cell

Use the paired Bernoulli switching contract in `switching_noisy_information_lower_bound_v1.md`:
losses are `Y_t` and `1-Y_t`, the null is IID `Ber(1/2)`, and under onset `nu` the outcomes are
IID `Ber(1/2+epsilon)` from `nu` onward. There is a pathwise cap `B` on queries, each label is
released at the start of event `s+d`, and a global false-promotion event has null probability at
most `alpha`. The learner acts before the current event outcome. Compare with the oracle that
switches once at the true onset and pays at most `k`.

Freeze `T=120`, `B=20`, `epsilon=1/10`, `alpha=1/20`, `k=1/10`, delays `d in {1,5,20}`, and a
uniform prior over `nu in {1,...,T}`. Query price is nonnegative and omitted from this lower
bound. No other parameter cell is authorized by this registration.

## Registered bound

Let `A_t` be the installed action at round `t`. Under the null,
`P_0(A_t=1)<=alpha`, since action 1 implies that a false promotion has already occurred. For a
fixed `t`, condition the onset prior on `nu<=t`; this is a uniform mixture of the `t` alternatives
that are active at round `t`. The transcript through the action at `t` has, under alternative
`nu`, KL divergence from the null at most

`kappa * n_(nu,t)`, where `kappa=KL(Ber(1/2+epsilon)||Ber(1/2))` and
`n_(nu,t)=min(B,max(0,t-nu-d+1))`.

By convexity of KL in its first argument, the mixture transcript divergence is at most
`kappa * (1/t) sum_(nu=1)^t n_(nu,t)`. Binary data processing for `A_t` and the common null
probability at most `alpha` then bounds the mixture probability of action 1 by
`beta_alpha(kappa * (1/t) sum_(nu=1)^t n_(nu,t))`, where
`beta_alpha(x)=sup{q>=alpha: kl_Ber(q||alpha)<=x}`.

Under onset `nu`, the per-round expected loss gap is `2*epsilon*P_nu(A_t=0)` for `t>=nu`.
Summing and averaging the uniform onset prior therefore yields the registered gross-regret lower
bound

`LB_mix = (2*epsilon/T) sum_(t=1)^T t * [1-beta_alpha(kappa*(1/t)*sum_(nu=1)^t n_(nu,t))]`.

The net-cost excess is at least `LB_mix-k`; query and learner switch costs are nonnegative. This
bound applies to every adaptive randomized query and switching policy satisfying the hard cap and
global null-risk contract. It is an average-onset bound; consequently it is also a lower bound on
worst-onset regret. It does not exploit the joint geometry of the action events across different
times, so it is not asserted to be the optimal unknown-onset lower bound.

The comparison quantity is the average over all onsets of the existing per-onset bound in
`switching_noisy_information_lower_bound_v1.md`, evaluated under the same parameters. The mixture
bound is useful as a sharpening only if it is numerically larger. Also report the earlier
registered onset `nu=61` value to show the scale but do not compare it directly to an all-onset
average. Invert the binary KL numerically with a bracketed root solve; record code hash and full
per-delay values. No policy is evaluated and no efficacy claim follows.

## Proof scope and prior-work screen

Only the adaptive KL chain rule, convexity of KL, binary data processing, and the binary-KL
testing tradeoff are used. This is a reduction for the present change-point contract, not a new
information inequality or an anytime-valid test. It closes neither the attainable-frontier gap nor
the source-level comparison to active sequential design. The lower bound grants the learner a
global false-promotion allowance separately in each single binary reduction, so it can remain
loose; the mixture averages onset hypotheses at each time but does not jointly optimize a test.

Reproduction is registered as `python scripts/evaluate_switching_unknown_onset_mixture_lower_bound.py`,
writing `outputs/switching_unknown_onset_mixture_lower_bound_v1/results.json`. A larger bound
than the average individual-onset bound sharpens the impossibility floor but is not itself a
methodological contribution. A non-sharpening result is still informative and must be recorded.

## Executed result and decision

The frozen calculation completed. For delays 1, 5 and 20, the mixture gross lower bounds are
`8.40640`, `8.55403` and `9.10782`; the averages of the existing individual-onset gross bounds
are `8.47296`, `8.68361` and `9.40558`. Thus the mixture reduction is weaker by `0.06656`,
`0.12959` and `0.29776`, respectively. Its net bounds subtract the same switch charge `k=0.1`.
For reference only, the onset-61 gross bounds are `8.429`, `8.658` and `9.516` up to displayed
rounding. The numerical script passed Ruff, records its SHA256, and saved the timewise inputs and
all three comparisons in `outputs/switching_unknown_onset_mixture_lower_bound_v1/results.json`.

Decision: convexifying the onset alternatives before binary data processing does not sharpen the
current lower bound. The reason is visible in the calculation: averaging KL per active onset
weakens the testing constraint enough to outweigh the benefit of using one shared null event.
Keep this as a checked non-result. Do not tune the prior or parameter cell post hoc. The unknown-
onset attainability question remains open; the next useful comparison is a source-level reduction
of established active sequential testing into the exact paired, delayed contract, including the
same global conditional-null event and pathwise request accounting. No efficacy gate is passed.
