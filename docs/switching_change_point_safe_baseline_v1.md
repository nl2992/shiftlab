# Anytime-valid change-point mixture with delayed queried labels

2026-10-28. **Status:** established safe detector specialization and mandatory comparison
baseline; no acquisition or switching novelty claim.

## Source audit

Shin, Ramdas and Rinaldo, “E-detectors: A Nonparametric Framework for Sequential Change
Detection,” New England Journal of Statistics in Data Science 2(2), 229–260 (2024),
[full primary article](https://nejsds.nestat.org/journal/NEJSDS/article/59/text),
[DOI](https://doi.org/10.51387/23-NEJSDS51). The full 32-page published source was downloaded
and extracted. I inspected Sections 2.1–2.5 and 2.7, the e-detector mixture and false-alarm
statements, and the likelihood-ratio and delay discussion. Relevant results are: Proposition 2.3
(mixtures of e-detectors remain valid), Theorem 2.4 (thresholding gives ARL control), the
weighted-start construction in Section 2.3 (initial weights summing to at most one control
probability of any false alarm), and Proposition 2.14 (a likelihood-ratio expected-delay bound
under its stated iid post-change assumptions). The paper explicitly includes Lorden-style tests
started at consecutive times and explains their e-detector representation. This is a source-text
fidelity audit, not independent verification of the proofs. Local PDF/text hashes are in source
manifest v13.

## Exact ShiftLab specialization

Use `Y_t in {0,1}` with null `E[Y_t | F_(t-1), C_t, Q_t] <= 1/2`, where querying is chosen
before `Y_t`. For a known Bernoulli alternative `Y_t~Ber(1/2+epsilon)`, define
`Z_t=2Y_t-1` and the likelihood-ratio factor

`L_t=(1+2*epsilon)^{Y_t} (1-2*epsilon)^{1-Y_t} = 1+2*epsilon*Z_t`.

For each candidate onset `tau=1,...,T`, let `M_n^tau` start at one before `tau` and multiply by
`L_s` only for queried event times `s>=tau`, using factor one when unqueried. Under the full
conditional null, every `M^tau` is a nonnegative event-time supermartingale despite predictable
query skipping. Choose fixed weights `w_tau>=0` with `sum_tau w_tau=1`, and set

`M_n = sum_tau w_tau M_n^tau`.

This is again a nonnegative supermartingale starting at one. Promote when the mixture visible from
released labels first exceeds `1/alpha`. With fixed known delay `d` and order-preserving release,
the visible statistic at the start of round `t` is exactly the event-time statistic `M_(t-d)`
(with the empty prefix before `t=d+1`). A visible crossing is therefore contained in
`{sup_n M_n>=1/alpha}`, so Ville gives probability of any false promotion at most `alpha`.
Every query schedule predictable under the stated filtration is allowed, and a pathwise cap
`sum Q_t<=B` does not change validity. For repeated promotions, allocate episode levels
`alpha_e` with `sum_e alpha_e<=alpha`, reset each episode, and use only labels queried after its
start; old pending labels cannot be counted as fresh evidence.

For a finite known horizon, `w_tau=1/T` gives a uniform onset mixture. Under a post-change
Bernoulli stream beginning at `nu`, the `nu` component has likelihood-ratio log drift
`kappa=KL(Ber(1/2+epsilon)||Ber(1/2))`. If at least `m` post-change queried labels have arrived,
the mixture is at least `w_nu M^nu`; hence crossing is guaranteed whenever that component reaches
`1/(alpha*w_nu)`. With queries every round after the onset, Proposition 2.14 gives the source's
expected sample-delay bound for that component under its iid conditions, with threshold
`c=1/(alpha*w_nu)`; fixed label delay adds `d` calendar rounds. A hard cap that expires before
crossing truncates this guarantee. This is a detector reference, not an acquisition policy.

## Novelty consequence and limits

The following are established ingredients: restarting a test at each possible onset; summing or
mixing the resulting evidence; a weighted start penalty for unknown onset; likelihood-ratio betting
for a specified Bernoulli shift; and an anytime false-alarm guarantee. This directly addresses a
fixed monitoring-window miss at the *detection* layer. Its guarantee neither pays for queries nor
chooses their timing, establishes current/future profitability, or controls losses before a
rollback. A global no-benefit null is false during favorable regimes, and retaining old wealth
does not certify current value.

Therefore compare acquisition and deployment rules on top of this change-point mixture under
identical query budget, delays, utility and switch costs. Any advantage must come from a provably
better economic acquisition/deployment decision, not the onset mixture or likelihood-ratio factor.
The mixture is standard evidence machinery and is not the sought algorithm.
