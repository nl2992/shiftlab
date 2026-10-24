# Current-covariate bounds under a population-average null

## Result

For the registered target

\[
\mathbb E[H_t\mid\mathcal F_{t-1}]\le 0,
\]

where current features are revealed after \(\mathcal F_{t-1}\), a bounded betting factor
normalized by a bound selected from the current feature vector is not generally a
supermartingale factor. “The bound is chosen before the label” is insufficient. Such a factor
requires the stronger null conditional on the information used to choose that bound, or another
explicit model of the joint current-feature/outcome distribution.

For a PPI contrast

\[
\widetilde H_t=h_t+\frac{Q_t}{q_t}(Z_t-h_t)-\epsilon,
\]

the query randomization gives \(\mathbb E[\widetilde H_t\mid\mathcal F_{t-1},X_t]
=\mathbb E[Z_t\mid\mathcal F_{t-1},X_t]-\epsilon\), assuming the proxy and propensity are
formed before the query coin and outcome. The registered marginal null controls the average of
these conditional means over \(X_t\); it does not require each conditional mean to be nonpositive.
Dividing \(\widetilde H_t\) by \(B(q_t)\), with \(q_t=q(X_t,\mathcal F_{t-1})\), changes the
weighted average being tested.

## Exact one-step counterexample

Let \(X\) be equally likely to be 0 or 1 and let \(H=1\) when \(X=0\), \(H=-1\) when
\(X=1\). Then \(\mathbb E[H]=0\). Choose current-context bounds \(B(0)=1\) and \(B(1)=2\).
For stake \(\eta=1/2\), the proposed factor has expectation

\[
\mathbb E\left[1+\eta H/B(X)\right]
=\tfrac12(1+\tfrac12)+\tfrac12(1-\tfrac14)=\tfrac98>1.
\]

The exact diagnostic is covered by
`tests/test_propensity_floor_bound_development.py::test_covariate_dependent_scaling_can_break_a_marginal_null`.

## Valid scope and project decision

If \(|H_t|\le B\) for a fixed bound and \(\eta_t\in[0,1]\) is predictable from past
information, then \(1+\eta_t H_t/B\ge0\) and

\[
\mathbb E[1+\eta_t H_t/B\mid\mathcal F_{t-1}]
=1+\eta_t\mathbb E[H_t\mid\mathcal F_{t-1}]/B\le1.
\]

Thus the fixed-support process remains valid for the registered marginal estimand. A
current-context-specific scale can be studied under the stronger conditional null
\(\mathbb E[H_t\mid\mathcal F_{t-1},X_t]\le0\), but that is a different scientific target and must
be registered, calibrated, and evaluated separately. No eventwise-bound result from the
propensity-floor grid is evidence for the marginal-null claim.

The fixed 0.10-bound sensitivity in the CUDA development grid explained much of the earlier
uniform-versus-adaptive detection gap. That does not make eventwise scaling valid and does not
establish an adaptive-query advantage. The report and protocol are
`outputs/propensity_floor_bound_development_60/reports/propensity_floor_bound_development.md`
and `docs/propensity_floor_bound_development_protocol.md`.

The next theorem task is to compare mathematically valid fixed-bound betting and established
variance-sensitive processes under the same original null, filtration, hard budget, and labels.
Do not spend another grid on current-context rescaling unless the estimand is explicitly changed or
a valid joint-law argument is added.
