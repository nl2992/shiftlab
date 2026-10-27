# Anytime-valid Optimal Policy Identification applicability audit

**Audit date:** 2026-10-26  
**Disposition:** include as a required direct Q2 comparator; do not claim a ShiftLab reproduction or real-data result yet.  
**Primary source:** Molitor, *Anytime-valid Optimal Policy Identification*, arXiv:2606.17515v1 (16 June 2026), CC BY 4.0.  
**Reference implementation inspected:** `dmolitor/av-policy-selection`, commit `6385218f57aaf5a2ad3d9bd02145c6c3125fd593`.

## Method and guarantee

The paper considers a fixed finite class of policies evaluated from sequential logged contextual-bandit observations `(X_t, A_t, R_t)`. Rewards lie in `[0,1]`; the logging policy is predictable from prior history and its action probabilities are available; each target policy is supported by the logger. Its central stationarity condition is that every target policy has a time-invariant value `nu_t(pi)=nu(pi)`. A reward model used in the doubly robust pseudo-outcomes must be predictable, meaning fitted from history available before the current reward. The policy-value confidence sequences are combined across the finite class to form a candidate set that retains every optimal policy uniformly over time with probability at least `1-alpha`. With one-sided lower and upper bounds, a direct union-bound implementation allocates `alpha/(2 |Pi|)` to each endpoint; see the source-code/alpha-allocation caveat below. A unique best policy can be selected when its lower bound exceeds every competitor's upper bound. The paper's sample-complexity statement additionally assumes linear growth of its variance process; strict overlap is given as one sufficient condition.

This is already a strong anytime-valid solution to sequential identification of the best policy in a finite logged contextual-bandit class. It materially narrows any claim that ShiftGuard is the first system to sequentially certify a preferred policy. It does not by itself solve a monitor-triggered shift-to-harm test, costed label acquisition, candidate retraining, switching-cost optimization, or a complete monitor-certify-deploy-fallback controller. Those are possible integration questions, not established gaps or novelty claims.

For a finite class of size `m`, simultaneous two-sided coverage requires allocating error over both tails and all policies. The independent implementation uses `alpha/(2m)` per one-sided endpoint; this preserves the direct union-bound target of global error `alpha`.

## Code audit and provenance

The official repository was shallow-cloned outside the project tree for read-only inspection at commit `6385218f57aaf5a2ad3d9bd02145c6c3125fd593`. Its `PolicySelector` computes the paper's candidate-set rule and first strict separation stopping time from supplied lower/upper confidence-bound arrays. Its confidence-sequence module contains the linked LIL/PrPl/betting formulas. The repository has no top-level license file in the inspected checkout; no code was copied or vendored. The paper itself is CC BY 4.0. This was a source audit, not an execution or reproduction of the paper's figures.

**Reference experiment-code caveat:** inspection of the pinned `simulations.py` and `reanalysis.py` found that their OLS reward predictor is fitted once on the complete evaluation stream (`predictor.fit(contexts, actions, rewards)`) and then used to construct every time-indexed pseudo-outcome. That is not predictable with respect to the paper's history filtration at times before the final observation. The paper's Section 2.3 explicitly requires the reward model at time `t` to be built from `H_{t-1}`. Both files also clip the complete AIPW score to `[0,1]`, rather than applying the paper's stated weight-dependent truncation to the reward-model component; clipping an unbiased DR score generally changes its expectation. The real-data reanalysis additionally replaces zero propensities with one before calculating weights, then retains unsupported candidate policies (the source comments acknowledge that some policies are not eliminated before the zero-support batch). A confidence sequence cannot restore support or predictability lost in its input scores.

There is also an alpha-allocation mismatch in the inspected simulation/reanalysis calls. The paper's base LIL result is one-sided; its text says a two-sided CS requires splitting error across lower and upper tails. The author code passes `alpha / m` to both one-sided bounds. A direct union bound over `m` policies and two tails then controls simultaneous coverage at `2 alpha`, not `alpha`, absent an additional dependence argument. The OPI candidate-set theorem is stated at level `1-alpha`; a guarantee-preserving implementation should use `alpha/(2m)` per one-sided endpoint. This is recorded as an implementation/proof-bookkeeping discrepancy requiring resolution, not as a blanket refutation of the paper's theorem.

An exact counterexample illustrates the clipping issue without purporting to quantify bias in the paper's data: let the target always choose action 1, the logger choose each action with probability `1/2`, reward under action 1 be Bernoulli(`0.9`), and the reward prediction be the predictable constant `0.5`. The unclipped DR score has expectation `0.9`. The reference-code operation `clip(w*(R-rhat)+rhat, 0, 1)` has expectation `0.70` (`0.45` from logged action 1 plus `0.25` from action 0), so it is not generally an unbiased pseudo-outcome. This counterexample only establishes that the source operation does not preserve the required moment condition in general; it does not estimate the magnitude of any bias in the paper's reported examples.

These findings concern the inspected implementation paths and alpha bookkeeping, not a blanket refutation of the paper's theorem under its stated conditions. Do not label author-code outputs a faithful implementation of the theorem without resolving these issues. Any ShiftLab comparison should implement the paper's bounded DR pseudo-outcomes independently, use a genuinely predictable reward model (or an independently trained frozen model), enforce support, allocate error across both tails and policies, and test the conditional-mean identity before computing confidence sequences.

Inspected source hashes (SHA-256):

| File | SHA-256 |
|---|---|
| `src/av_policy_selection/policy_selection.py` | `cce8a6bda137b6da903f11355b16fb757744064172d9ff601daa21174eca2558` |
| `src/av_policy_selection/confidence_sequences.py` | `e4c8a579d958f4a744a4be20b63e33a6900a0126fe5bddd25980ff158bd296bf` |
| `src/av_policy_selection/reward_predictors.py` | `0fa8dc22c341e806c27b92815016db57c221c57e0daeacde2f30d8f91ae48901` |
| `simulations.py` | `6932f68e61d1d1b9d7b7080b721adb807d2c2b0064307d1d4972b9cd0b831f71` |
| `src/av_policy_selection/reanalysis.py` | `c8307a3af253ef670609e0019059d3e71062e629408c12e4f46965b8fba55533` |

## ShiftLab task fit

**Best current candidate: Open Bandit Dataset (OBD), fixed-horizon offline Q2 development only, conditional on a narrower position-level estimand.** OBD contains logged item, position, click reward, recorded action propensity, impression timestamp, and context features. The complete Random/all archive has 1,374,327 rows over seven UTC days and constant recorded propensity `1/80`; this is much better conditioned than BTS, whose propensity distribution has an extreme lower tail. The existing audit nevertheless records that the archive count differs from the paper, complete-slate/user identifiers are unavailable, feature as-of availability is unresolved, and click-release timing is not documented.

An OPI comparison could be considered only for a preregistered finite class of **position-level item policies** with `[0,1]` click reward, known per-decision propensities, and no use of unresolved affinity features. It cannot be described as slate-policy evaluation: the released representation lacks complete slates, and the source paper itself warns that item-position reward models may fail when simultaneously displayed items interact. A position-level analysis would need to state this no-interference/reward-factorization assumption and include sensitivity analysis or restrict its claim accordingly. The seven-day window must be checked for material policy-value drift before using OPI's time-invariant-value guarantee; a retrospective event-time replay would still not establish prospective label-arrival validity.

**Current decision: eligible for protocol development, not yet eligible for a validity-bearing OPI run.** Freeze candidate policies, action and context definitions, time blocks, reward maturity, feature availability, stationarity diagnostic, and inference unit first. The Random logger is a candidate because its recorded propensity is bounded; it does not cure the slate/interference, timestamp, or version-reconciliation issues. Do not use current BTS IPS/DR point estimates as a substitute for OPI or claim its confidence-sequence guarantee from those estimates.

## Comparison contract if the OBD gate is later passed

1. Freeze one finite candidate-policy class before scoring and reserve whole UTC days for a held-out event-order replay.
2. Use only context available before the impression; omit the 80 past-affinity features unless their as-of construction is verified.
3. Verify the exact action probability represented by each logged propensity at the chosen position and the data collection unit. Preserve any clustering/dependence in uncertainty calculations.
4. Define reward as click probability/value only. Keep imposed switch or compute costs separate and do not call click value net business utility.
5. Compare OPI's time-uniform candidate set/stopping rule with a fixed-horizon sample-split OPE selector, the registered Target-Scout analogue only where its feedback contract matches, and no-change. Use shared data, candidates, and resource accounting.
6. Evaluate stationarity and overlap on development days; report any failure as an applicability result, not a tuning opportunity on the held-out days.
7. Independently verify coverage and stopping behavior on registered synthetic logged-bandit controls before making any guarantee claim.

An independent stationary synthetic calibration was subsequently run; its protocol and results are in `opi_calibration_protocol_v1.md` and `../../outputs/shiftguard_unified/sota_reproductions/molitor_opi_calibration_v1/`. No real-data OPI metrics or guarantee are claimed.

In 1,000 all-tied null streams, neither the familywise-correct nor the author-style per-tail allocation ever removed a true optimum or stopped on a unique policy (0/1,000; exact 95% upper bound 0.368%). On the unique-best alternative, the familywise-correct allocation stopped by 2,000 events on 800/1,000 streams and ended with the correct singleton on 786/1,000; the author-style allocation did so on 938/1,000 and 931/1,000. The latter is more powerful in this DGP, as expected from its less conservative tail budget, but 1,000 null replications with zero errors do not establish that its larger nominal familywise error is harmless. This is a controlled synthetic implementation check, not OBD or external confirmation.

## Sources

- [Molitor, *Anytime-valid Optimal Policy Identification*, arXiv:2606.17515v1](https://arxiv.org/html/2606.17515v1)
- [Official author implementation](https://github.com/dmolitor/av-policy-selection)
- [ShiftLab OBD readiness audit](open_bandit_data_readiness_audit.md)

## Matched candidate-gate comparison update (2026-10-26)

The independent implementation was compared with the pinned official MOPE gate and fixed-horizon controls on 1,000 tied-null and 300 unique-best streams, horizon 200. OPI had zero false optimum eliminations in the null but found no singleton in the unique-best alternative at this short horizon. MOPE's gate promoted 11/1,000 null streams and 279/300 fixed-candidate alternatives; three null confidence paths became empty and were independently reconstructed as coverage-failure diagnostics. The candidate gate and finite-class policy identification have different targets, so these results do not rank them head-to-head. They establish only this synthetic behavior, not OBD or real-data validity. See `opi_mope_matched_results_v1.md` and the [matched output](../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/report.md).