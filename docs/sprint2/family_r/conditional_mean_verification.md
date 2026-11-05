# R2 verification: what `choe_ramdas_eb` computes, and the conditional-mean e-process used in R2

Sources read for this note:
* the code: `scripts/sota_sprint/fam_x.py`, `scripts/failure_atlas_v2_flq/qce.py` (`DiscernQCE`,
  `_QCECertMixin`) and `scripts/promising_directions/sota/competitors/certificate_stops.py`
  (`DiscernStyleStop`, `PrPlEBCS`);
* Choe & Ramdas, arXiv:2110.00115, HTML version, first 100k characters only. Sections 4.4 and
  Appendix A.1, which hold the explicit weak-null e-process formulas, were **not** read.
* `docs/sota_sprint/novelty_audit.md`, for Henzi & Ziegel (arXiv:2103.08402) and Waudby-Smith et
  al. 2022. Henzi–Ziegel itself was **not** re-read in this session.

What the paper states, as read: the target is `Delta_t = (1/t) sum_{i<=t} E_{i-1}[delta_i]`. The
e-processes test the **weak null** `(1/t) sum_{i<=t} E_{i-1}[delta_i] <= 0` for all t. This is
contrasted with Henzi–Ziegel's **strong null**, under which one forecaster is better at every time.
The CS is built from fixed-lambda exponential processes `exp{lambda S_t - psi(lambda) V_t}`, with
boundaries from the method of mixtures. Validity rests only on the martingale structure, with no
stationarity assumed, but every delta must be bounded (`|delta| <= c/2`).

## 1. What the existing `choe_ramdas_eb` port computes

`choe_ramdas_eb` is `DiscernQCE(T, B, alpha, rng=r("choe_ramdas"))`, and `+front` adds `front=True`.

1. **Recorded stream.** `_QCECertMixin.request_labels` creates a record only when a disagreement is
   actually queried (`take`). Agreements and unqueried disagreements never enter the CS. Each label
   enters with weight `w = 1`, in request order. The increment is `Y_k = d_{s_k}`, which is ±1 on
   the k-th queried disagreement.
2. **CS.** `PrPlEBCS(alpha, lam_max=.5)` is applied to `W_k = (Y_k + 1)/2` (`c = 1`). It is
   Waudby-Smith & Ramdas's predictable plug-in empirical-Bernstein CS: `lambda_k` comes from past
   `W` and is clipped to 0.5, with `v_k = 4 (W_k - muhat_{k-1})^2`. Each side is compared with
   `2/alpha`, and the CS is the running intersection.
3. **Rule.** It stops and deploys the challenger the first time the lower bound on `2W - 1` exceeds
   0 (`safe`). It stops and keeps the incumbent the first time the upper bound falls below 0
   (`regression`). Acquisition then ends. Acquisition is paced with `p_min = .05`, or `q = 1` while
   undecided for `+front`.
4. **The null it controls.** The bets are predictable, so the lower-side process is a
   supermartingale under `H: E[W_k | G_{k-1}] <= 1/2` for every k. That is the **pointwise
   query-conditional** null, the Henzi–Ziegel-type strong null on the queried subsequence. Under a
   time-varying mean, the bound needs `sum_k lambda_k (mu_k - 1/2) <= 0`. That sum is weighted by
   data-dependent predictable bets, so the unweighted running-average (weak) null does not imply it.
   On ±1 outcomes the product `prod(1 + lambda_k x_k)` is the same Bernoulli likelihood-ratio form
   as QSG's started mixture, but this port uses no starts.

## 2. How it differs from a faithful time-averaged conditional-mean test

| | `choe_ramdas_eb` port | faithful Choe–Ramdas weak null under a label budget |
|---|---|---|
| events averaged | queried disagreements only (selection by `q`) | **all** events: agreements have `d = 0`, unqueried disagreements need IPW |
| null | pointwise (or lambda-weighted) query-conditional mean <= 0 | `sum_{i<=t} E[d_i \| G_{i-1}] <= 0` for every t (unweighted) |
| bet | predictable plug-in lambda_k | **fixed** lambda (a mixture over a fixed grid) or a mixture boundary; a predictable lambda reweights the average |
| range | `[-1, 1]` with weight 1 | IPW `L/q` has no a priori bound. Bounded EB needs `q >= q_min`; betting on the nonnegative `Y = L r / q` needs no bound |
| starts | none | none. A started mixture tests every window, which is equivalent to the pointwise null |

If the query rule reacts to past outcomes, so that it queries more when the challenger has been
winning, the query-average and the event-average weight time differently. Under a nonstationary
weak null, the port can then reject when the faithful test should not, and the reverse can also
happen. In the CAMS/D2 host this effect turned out small in practice: CAMS queries almost every
disagreement (`u ~ 1`) until the budget is gone (measured below).

## 3. The R2 construction (implemented in `fam_r.CondMeanEP` + `RGate(evidence="cmi")`)

* `Y_k = 1/2` on an agreement. On a disagreement, `Y_k = L_k r_k / q_k`, with `r_k = 1[challenger
  correct]` and `q_k = u_k + (1 - u_k) q_gate_k`. Both propensities are frozen at issue.
* `E_t = mean_j prod_{k<=t} (1 + lambda_j (Y_k - 1/2))`, with the fixed grid
  `lambda_j in {.02, .05, .1, .2, .35, .5, .7, 1, 1.3, 1.6}`.
* **Clock and filtration:** the implementation advances on the ordered issue/disagreement queue,
  not on label-release time or an unqualified wall-clock event index. Before the label for a queued
  event, the filtration may include prior released outcomes, current model predictions, host rank,
  and the frozen union query probability `q`; the paired loss sign is revealed only by the label.
  Agreements contribute `Y=1/2` and factor one, so omitting them leaves the product unchanged.
* **Null `H_CM`:** `sum_{k<=t} mu_k <= 0` for every prefix of that issue/disagreement clock, where
  `mu_k = E[d_k | G_{k-1}] = 2 E[Y_k | G_{k-1}] - 1`. This is the time-averaged conditional-mean
  null on decision-relevant disagreement events under the stated filtration; it is not a generic
  all-event or marginal null.
* **Proof sketch.** Write `a_k = E[Y_k | G_{k-1}] - 1/2`, which lies in `[-1/2, 1/2]`.
  1. `M_t = prod (1 + lambda (Y_k - 1/2)) / prod (1 + lambda a_k)` is a positive martingale,
     because `1 + lambda a_k >= 1 - lambda/2 > 0`.
  2. Jensen gives `sum log(1 + lambda a_k) <= t log(1 + lambda abar_t) <= 0` under `H_CM`.
  3. So the e-process is at most `M_t` at every t, and Ville's inequality holds. A mixture over
     fixed lambda keeps the bound.
  4. Wealth stays positive for every lambda < 2, however large `1/q` is. This is the nonnegative
     betting device of Waudby-Smith et al. 2022.
* **Frozen when unidentifiable.** At the first queued disagreement with `q_k = 0` the whole CMI
  process is frozen, because that difference is not identifiable. That point is budget exhaustion,
  or CAMS `u = 0` with no gate query. A stopped process keeps the Ville bound.
* **Discard test.** It is mirrored, with `Y' = L (1 - r) / q`.
* **Promotion.** D2's rule: the crossing `E >= 2/alpha` is latched, and the challenger is promoted
  once CAMS ranks it first.
* **Unit tests** (`tests/sprint2/test_fam_r.py`):
  * the exact IPW factor mean;
  * the exact expectation `<= 1` by enumeration on a weak-null path where the pointwise null fails;
  * Monte Carlo validity on that path, where QSG's started mixture rejects at least 50% of the time;
  * IPW validity under an adaptive propensity;
  * freezing.
* **Ablation `R2-qc`.** The same fixed-lambda product on query-conditional `z`. Its null is
  `sum_{n<=m} (P(z_n = 1 | G_{n-1}, queried) - 1/2) <= 0` for every m: the weak null on the queried
  subsequence.

Measured on the host: on development seeds, CAMS + gate propensities on pre-verdict disagreements
were 1 until the budget ran out. Every q below .1 was exactly 0, which means the budget was
exhausted (4 seeds each, on F0_null, F0_better and F7_near_better). So in D2's host the IPW weights
are 1 before exhaustion. R2 and R2-qc then differ mainly in where they freeze: R2 stops at budget
exhaustion, while R2-qc ignores unqueried events.

## 4. Track V statement

R2, R2-qc and R2-floor25 are **V1**. They control the weak conditional-mean null. It does **not**
hold on the Markov nulls F5_dep_null_*: there the running conditional mean is positive along runs.
It also fails on the real twin streams. Promotions there count as false only against the marginal
(V2) null, which these methods do not test. Rates on those streams are reported as a risk check,
not as a validity failure.
