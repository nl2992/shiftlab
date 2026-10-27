# Prediction-Powered E-Values: paper-to-code audit

**Audit date:** 2026-10-26. **Primary source:** Csillag, Zrnic, and Ramdas,
[*Prediction-Powered E-Values*](https://proceedings.mlr.press/v267/csillag25a.html),
ICML 2025, PMLR 267, 11493–11514. The PMLR record links the authors' software
repository, but that link returned 404 during this audit. The paper PDF remains
available from the PMLR page and [arXiv](https://arxiv.org/abs/2502.04294).

## Published construction

Let a valid base e-factor (e_t(Y_t)) be selected predictably and lie in a
known interval ([a_t,b_t]), where (a_t>0). A cheap proxy
(e_t(\widehat Y_t)) is available for every event. The label indicator
(I_t\sim\mathrm{Bernoulli}(q_t)) is drawn with known, predictable
propensity. The paper replaces the base factor by

\[
\widetilde e_t=e_t(\widehat Y_t)+
\frac{I_t}{q_t}\{e_t(Y_t)-e_t(\widehat Y_t)\}.
\]

The correction preserves the base factor's expectation under the stated
sampling design. The paper's positivity condition is
\[
q_t\ge 1-a_t/b_t,
\]
which ensures the corrected factor cannot be negative for any allowed proxy
and observed factor. Products of the corrected factors retain the e-process
validity argument when the base process is valid and the proxy, propensity,
and query randomization obey the paper's filtration and sampling conditions.
Models and query policies can update only from information available before
the current outcome. The procedure does not repair an invalid base null or
informative outcome-dependent query selection.

## Paired decision-cost transfer

For the synthetic paired-cost comparison, let (Z_t) be deployed-minus-reference
cost centered by the declared harm margin, with (|Z_t|\le B). Under the
eventwise conditional-mean null, a base factor is
\[
e_t(Z_t)=1+\lambda Z_t/B.
\]
The proxy is a frozen pre-monitor prediction of the paired cost, clipped to
the same support. With (lambda=0.1), factors lie in ([0.9,1.1]), and the
required query floor is (1-0.9/1.1\approx0.18182). Thus both registered
query rates (q=0.20) and (q=0.40) satisfy the positivity requirement.
This deliberately uses one fixed stake at both rates; it is a conservative,
paper-based adaptation to the paired decision-cost endpoint, not a reproduction
of every application in the PPE paper. The label must reveal the paired
potential costs under the same outcome. If the deployed action changes the
outcome and the counterfactual reference cost is unavailable, this construction
does not identify the paired estimand.

## Local implementation and checks

`src/shiftlab/dive/prediction_powered_evalues.py` implements the published
factor correction, propensity floor, and product process. The function rejects
an unqueried outcome supplied to the learner, invalid factor support, and
propensities below the positivity threshold. `src/shiftlab/dive/risk_proxy_monitor_grid.py`
adds `ppe_fixed_stake` to the matched synthetic monitor comparison, with the
same event paths, uniform query paths, hard label-cost stopping rule, proxy,
null cells, and alternatives as the existing inverse-propensity PPI and direct
monitors. The paired-cost RMSE remains a separate estimator diagnostic; PPE
alarms use the corrected base e-factors.

Six CPU tests verify the formula, exact conditional-mean identity, stake/query
threshold, extreme nonnegativity boundary, outcome omission, and wealth
product. Focused pytest, Ruff, and mypy pass. This is an implementation audit
and development comparator only. It does not establish type-I control outside
the base conditional-mean and randomized-query assumptions, and no efficacy or
superiority claim is made until the registered comparison and independent
null calibration are complete.

## Fidelity decision

Classify this as a **faithful implementation of the PPE factor transformation
and a project-specific paired-cost adaptation**. It is not an end-to-end
reproduction of the paper's application experiments because the authors'
linked code was unavailable during the audit and the scientific endpoint here
is paired decision harm. The implementation preserves the published
nonnegative correction and query floor rather than substituting the repository's
inverse-propensity PPI estimator. Do not call the paired-cost experiment a
PPE reproduction or novelty result.

## References

- [PMLR paper and supplemental material](https://proceedings.mlr.press/v267/csillag25a.html)
- [arXiv paper](https://arxiv.org/abs/2502.04294)
- [Authors' software URL linked from PMLR](https://github.com/dccsillag/experiments-prediction-powered-evalues) (returned 404 on audit date)
