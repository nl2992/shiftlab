# Chugg group betting: paper-to-code audit

**Scope.** Formula-level audit of the standard per-stratum bounded-mean wrapper in
`src/shiftlab/dive/stratified_harm_eprocess.py`. This documents a standard composition; it makes no
novelty claim and reports no data or experimental results.

## Primary sources and read coverage

- Chugg, Cortes-Gomez, Wilder, and Ramdas, [*Auditing Fairness by Betting* (NeurIPS 2023),
  official proceedings PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/1338c277525011f20166cf740952bb47-Paper-Conference.pdf).
  Read the full 22-page official paper, including Appendix B, “Auditing multiple groups.” The
  PDF defines group fairness through equality of conditional mean predictions, then tests
  adjacent-group mean equality in parallel with level `alpha/J` per game; Ville plus a union bound
  controls the familywise type-I error at `alpha` (Appendix B, Proposition 5). The official PDF
  pagination is 22 pages.
- Vovk and Wang, [*E-values: Calibration, combination, and applications* (Annals of Statistics
  2021; arXiv full text)](https://arxiv.org/pdf/1912.06116). Read the full 48-page preprint,
  especially the definition of an e-variable, Section 3 on merging, and Section 5 on multiple
  testing. A fixed convex average of e-values is an e-value for the common/global null; the
  intersection of hypotheses can also be tested by averaging their null-valid e-values.

## Estimand comparison

Chugg et al. test equality of group means, e.g. `H0: mu_0 = ... = mu_J`, against at least one
inequality. The two-group betting score is based on a paired difference of predictions from two
groups, and Appendix B extends that equality-testing construction by testing adjacent pairs. Its
target is not the per-group paired decision-harm intersection null

```text
for each k: E[ Z_t | F_{t-1}, G_t=k ] <= 0,
Z_t = c(pi_t,Y_t) - c(ref,Y_t) - epsilon.
```

The adaptation here treats each fixed stratum's paired harm increment as its own bounded-mean
stream, `|Z_t| <= B_k`, and uses the existing `BoundedMeanEProcess` on the selected stratum's
subsequence. This requires the stratum and its fixed bound to be known before the increment,
and the conditional-mean null to hold for that stratum subsequence. The class checks the numeric
bound, not the null, filtration, paired-cost semantics, or predictability. In particular, it does
not turn Chugg's equality test into a published result for this one-sided paired-harm estimand.

## Composition encoded

Let `E_{k,t}` be the component e-process for stratum `k`, initialized at one, with fixed positive
weights `w_k` summing to one.

- **Fixed mixture:** `E_mix,t = sum_k w_k E_{k,t}`. Under the intersection null (all component
  processes are valid in the common filtration), this is an e-process. The selected alarm is
  `E_mix,t >= 1/alpha`. It tests the intersection/global null and does not identify which stratum
  caused an alarm.
- **Weighted Bonferroni:** reject if any `E_{k,t} >= 1/(alpha w_k)`. By Ville for each component
  and a union bound, the probability of ever falsely rejecting any true component is at most
  `sum_k alpha w_k = alpha`. This gives stratum-level alarms with familywise control when each
  component null is valid.

`StratifiedEProcess` stores the bounds, stratum weights, and combination choice at construction;
each update advances just one component. Untouched strata stay at `E=1`. Its optional
`adjusted_max_log_statistic = max_k(log(w_k) + log(E_{k,t}))` is the Bonferroni statistic: compare
it to `log(1/alpha)`. The mixture statistic is `logsumexp_k(log(w_k)+log(E_{k,t}))`. Both reduce
to the existing `BoundedMeanEProcess` for one stratum with matching stake settings.

**Disposition.** Per-group betting followed by fixed weighted Bonferroni and fixed convex-mixture
composition are standard constructions. Chugg et al. publish multi-group sequential betting for
equality of group means; Vovk and Wang establish fixed e-value mixture composition for a common
null. This code's paired decision-harm estimand is an adaptation of those ingredients. The
literature read here does not establish that this exact estimand-specific construction has or has
not appeared elsewhere; any stronger novelty statement requires a separate targeted search.
