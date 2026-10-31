# Onset-multiplicity lower bound and source audit (Failure Atlas family 1)

**Date:** 2026-10-30. **Status:** theory plus source audit, exploratory, **awaiting review** (protocol
Amendment 2 item 3: "a bound counts only after review"). **No novelty claim.** Numbers come from
`scripts/check_onset_multiplicity_bound.py` (CPU, seconds for Part A, about 40 s for Part B at 20000
paths, seeds 1/2/3). Nothing here is an atlas result and no atlas seed was touched.

Every step is tagged **[R]** (rigorous, derived below) or **[H]** (heuristic or unproved).

## 0. Summary

1. **Theorem 1 (finite-horizon packing bound) [R].** For labels that are independent Bernoulli, any
   stopping rule with null any-false-promotion probability at most `alpha` satisfies a
   change-of-measure inequality across `m` onsets. When the pre-onset law is at the null boundary,
   it gives the stated form:
   mean detection probability within `n` post-onset labels is at most `alpha + (nK + ln 2)/ln(m/(rho*alpha))`,
   with `K = KL(q1||q0)`. Equivalently, detection with probability `1-delta` needs
   `n >= [(1-delta-alpha) ln(m/(rho alpha)) - ln 2]/K`.
2. **The claim as stated in the task is false when the off state is harmful** (a pre-onset law
   strictly below `q0`). Pre-onset data then carry onset information. Section 4 gives the corrected
   statement (the reference law changes, so `K` becomes `KL(q1||q')` plus a pre-onset penalty) and a
   concrete valid gate (a context-triggered bettor) that avoids the `log m` cost in the toy
   experiment. All twelve ledger failure cells have a harmful off state (`q_off = 0.1`).
3. **Finite horizon caps the multiplicity.** With total label budget `N` and detection delay
   `n`, only `m ~ N/n` onsets are separable. The provable multiplicity term is `ln(N/n)`, not
   `ln(#starts)`: 1.7, 2.2 and 3.0 nats at `N=50, 100, 250` against 3.9, 3.5 and 3.6 nats for the
   started mixture.
4. **Source verdict: classical.** Huang and Veeravalli (arXiv 2511.12803) Theorem 1 states the same
   `log T + log(1/delta_F)` latency lower bound under a finite-horizon PFA constraint (asymptotically),
   and the repository's own `switching_finite_horizon_qcd_budget_delay_audit_v1.md` already holds the
   non-asymptotic KL/window-packing version. R2 kill rule: **not novel.**
5. **Implication:** Section 7.

## 1. Setting [R definitions]

Labels `X_1..X_N` (`N` = number of released labels; delays `d` only shift availability and are
ignored here). Null boundary `q0 = (1+h)/2 = 0.55`, `h = 0.1`. Filtration `F_i = sigma(X_<=i, U)`,
`U` an independent randomisation. A gate is a stopping time `tau in {1..N} U {inf}`.

* Null classes. `N_iid`: iid `Bern(q)`, `q <= q0`. `N_cond`: every `E[X_i | F_{i-1}] <= q0`
  (the class the repository's betting e-processes are valid for; `N_iid` is a subset).
  Validity `V(alpha)`: `Q(tau <= N) <= alpha` for every `Q` in the class. Theorem 1 uses only members of
  `N_iid`, so it holds for gates valid on either class.
* Alternative `A_k`: `X_i ~ Bern(q_off)` for `i < k`, `X_i ~ Bern(q1)` for `i >= k`, `q1 = 0.9`,
  `q_off <= q0`. Neutral: `q_off = q0`. (The atlas "neutral" off state is 0.5; it differs from `q0` by
  `KL(0.5||0.55) = 0.0050` nats per label.) Harmful: `q_off = 0.1`.
* `K(q') = KL(q1||q')`, `K0 = KL(0.9||0.55) = 0.2928` nats per label.

## 2. Theorem 1 and proof

**Theorem 1.** Let `V(alpha)` hold (iid-null validity suffices). Fix a window length `n` and onsets
`k_1 < ... < k_m` with `W_j = {k_j, ..., k_j+n-1} subset {1..N}`. Let `rho = max_t #{j : t in W_j}`
(`rho = 1` if `k_{j+1}-k_j >= n`). Let `q' <= q0` and
`B = (1/m) sum_j [ (k_j - 1) KL(q_off||q') + n KL(q1||q') ]`. Let
`p_j = P_{k_j}(tau in W_j)` and `pbar = mean_j p_j`. If `pbar > rho*alpha/m`, then

    kl(pbar || rho*alpha/m) <= B,                                   (1)

where `kl` is binary relative entropy. Consequently:

(a) `pbar <= (B + ln 2) / ln(m/(rho*alpha))`.                       (2)

(b) For every `j`, `P_{k_j}(tau < k_j) <= alpha`, so the mean probability of stopping by `k_j + n - 1`
is at most `alpha + pbar`.

(c) Neutral case `q_off = q' = q0` (pre-onset term vanishes): `B = n K0`, and detection by
`k_j + n - 1` with probability at least `1 - delta` on average forces

    n >= [ (1-delta-alpha) * ln(m/(rho*alpha)) - ln 2 ] / K0.      (3)

**Proof.**

*Step 1 (null mass of the windows) [R].* Let `R = Bern(q')^{iid}`. It is in `N_iid`, so `R(tau<=N)<=alpha`.
Events `E_j = {tau in W_j}` satisfy `sum_j 1_{E_j} <= rho * 1{tau <= N}`. Hence
`rbar := mean_j R(E_j) <= rho*alpha/m`.

*Step 2 (information through the window) [R].* `E_j` is determined by `(X_<=k_j+n-1, U)` because `tau`
is a stopping time. Under `P_{k_j}` and under `R` the first `k_j+n-1` labels are independent with
laws `Bern(q_off)` vs `Bern(q')` for the first `k_j - 1`, and `Bern(q1)` vs `Bern(q')` for the next `n`;
`U` has the same law. The chain rule gives
`KL(P_{k_j} || R on that sigma-field) = (k_j-1)KL(q_off||q') + n KL(q1||q') =: B_j`.

*Step 3 (data processing) [R].* For the indicator of `E_j`: `kl(p_j || R(E_j)) <= B_j`.

*Step 4 (convexity) [R].* `kl` is jointly convex, so `kl(pbar || rbar) <= mean_j kl(p_j||R(E_j)) <= B`.

*Step 5 (monotonicity) [R].* For `r < p`, `r -> kl(p||r)` is decreasing. Since `rbar <= rho*alpha/m < pbar`,
`kl(pbar || rho alpha/m) <= kl(pbar||rbar) <= B`. This is (1).

*Step 6 (explicit form) [R].* `kl(p||r) = p ln(p/r) + (1-p) ln((1-p)/(1-r)) >= p ln(1/r) - h(p) >= p ln(1/r) - ln 2`
(drop `(1-p) ln(1/(1-r)) >= 0`; `h` = binary entropy). With `r = rho alpha/m`, (1) gives (2).

*(b) [R].* Under `P_k`, the first `k-1` labels are `Bern(q_off)` iid with `q_off <= q0`; that law is in
`N_iid`, and `{tau < k}` depends only on those labels (and `U`). So `P_k(tau<k) <= alpha`.
Then `P_k(tau <= k+n-1) <= P_k(tau<k) + p_j`.

*(c) [R].* Set `q' = q0`, `q_off = q0`: `B = n K0`. From (2): `pbar <= (nK0 + ln2)/ln(m/(rho alpha))`.
Detection `>= 1-delta` implies `pbar >= 1 - delta - alpha` by (b). Rearrange. QED.

**Remarks.**

* Weighted onsets [R, same proof]. With prior weights `w_j`, use `sum_j w_j 1_{E_j}`: the null mass is at
  most `rho * w_max * alpha`, so `m` is replaced by `1/w_max`. The multiplicity term is the min-entropy
  `ln(1/w_max)` of the onset prior, divided by the overlap `rho`.
* Why `m` cannot be "the number of starts" [R]. With `N` total labels and window `n`, a separated
  family has `m <= N/n`. Closer onsets overlap (`rho ~ n/spacing`) and `m/rho ~ N/n` again. For the
  Failure Atlas, `N = B` (50, 100, 250). So the provable multiplicity is `ln(N/n)`, and a gate can
  legitimately thin its start grid (Section 6).
* Expected-count form (Theorem 2) [R]. Take `n_w = floor(N/m)` windows and nested events
  `E_j(n) subset E_j(n_w)` for `n <= n_w`. Then the same argument holds for each `n <= n_w` with the
  same `m`, and `sum_{n>=1} 1{tau >= k+n} = (tau~ - k)^+` with `tau~ = min(tau, N+1)` gives
  `mean_j E_{k_j}[(tau~ - k_j)^+] >= sum_{n=1}^{n_w} (1 - alpha - (nK0+ln 2)/ln(m/alpha))_+`.
  Conditioning on `tau >= k` only increases the left side. Numerically this is weak (3.3, 4.0 and 4.9
  labels at `N = 50, 100, 250`; Section 5) because it is linear in `n` while the true threshold behaviour
  is sharp. The quantile form (3) is the informative one. This is the "expected post-onset labels"
  statement the task asked for, with a constant factor loss.
* The factor `(1 - delta - alpha)` multiplies the log: it is `(log m + log(1/alpha) - O(1))/K` only
  for `delta, alpha` small.
  The `ln(1/alpha)` term enters through `ln(m/(rho alpha))`; the known-onset floor below is its
  `m = 1` case.
* Known-onset floor (Theorem 1 with `m = 1`, reference `Q_k` instead of `R`) [R, conditional-null
  only]. Take `Q_k` = `Bern(q_off)` before `k`, `Bern(q0)` from `k`. It is in `N_cond` for any `q_off <= q0`,
  and `KL(P_k||Q_k) = nK0` for **any** `q_off`. So under `V_cond(alpha)`,
  `kl(P_k(tau in W_k) || alpha) <= nK0`. For detection probability 0.9, `kl(0.8||0.1) = 1.36` gives `n >= 4.65`
  labels. This holds for the harmful case too. (Growth heuristic `ln(1/alpha)/K0 = 7.86` [H] is
  the usual "expected labels to accumulate `ln(1/alpha)` nats".)

## 3. Is the stated claim true? Pre-onset informativeness

The task's version reads: `E_k[(tau-k)^+ | tau >= k] >= (log m + log(1/alpha) - O(1))/KL(q1||q0)` for most `k`.

* **True [R]** in the neutral case (`q_off = q0`), in the quantile form (3), with the factor
  `(1-delta-alpha)` on the log and with `m` the number of `n`-separated onsets. It is false with `m` equal to
  the number of start positions that are closer than the delay (overlap, see Remarks).
* **False [R + toy] when the off state is harmful and the guarantee is against the simple null
  `P_0 = Bern(q0)^N` only.** Counterexample for the literal setting: `q_off = 0`, `q0 = 0.55`, `q1 = 0.9`.
  Gate: stop at the first 1 that follows a run of `r` zeros, `r = ceil(ln(N/alpha)/ln(1/0.45))`. Then
  `P_0(tau <= N) <= N * 0.45^r * 0.55 <= alpha`, and under `A_k` with `k > r`, `tau = k` with probability 0.9
  (one post-onset label), independent of `m`. The claimed bound for `m = 32`, `alpha = 0.1` is about
  `ln(320)/0.2928 ~ 20` labels. So the literal claim fails. It fails because `KL(P_k||P_0)` contains
  `(k-1) KL(q_off||q0)`, which is large, and because `P_0` alone is not a composite null.
* **With the composite null the counterexample dies** (the zero-run gate has false-promotion
  probability near `N/(e*r)` under `Bern(1/(r+1))`), but a different valid gate survives.
  Section 4.

## 4. Corrected statement for a harmful off state

**Corollary 1 (harmful off, composite null) [R].** Theorem 1 holds with any reference `q' in [q_off, q0]`.
Two natural choices:

| reference `q'` | `K(q')` per label | pre-onset penalty per label | what the bound says (N=50..250, detection 0.9) |
|---|---|---|---|
| `q' = q0 = 0.55` | 0.2928 | `KL(0.1||0.55) = 0.4534` | vacuous for `k_j` beyond a few labels |
| `q' = q_off = 0.1` | `KL(0.9||0.1) = 1.7578` | 0 | `n >= 3` labels, below the known-onset floor 4.65 |

So **the packing bound proves essentially nothing about onset multiplicity in the harmful-off cells.**
Both choices lose, and mixed references (`q' = 0.3`: 0.794 plus 0.116 per label) also give nothing
beyond the single-onset floor. I did not find a better *common* null for the packing step.

**Is the `log m` cost actually avoidable there? [H, with an explicit gate].** A predictable
(context-triggered) Kelly bettor is a valid e-process on `N_cond`: after `r` consecutive observed 1s it
bets stake `lambda = 0.778` (factor `1+0.818*lambda` on 1, `1-lambda` on 0), otherwise it does not bet.
The bet is `F_{t-1}`-measurable, so wealth is a test supermartingale for every `Q` in `N_cond`
(a bet factor `a` on a 0 and `(1-a(1-q0))/q0` on a 1 has conditional mean `<= 1` for all means `<= q0`);
by Ville, `P(wealth reaches 1/alpha) <= alpha`. With a harmful off state, runs of `r` ones are rare before the onset
(`0.1^r`), so the bettor needs no start mixture; with a neutral off state they are frequent
(`0.5^r`), the bettor loses wealth before onset, and the advantage disappears. Monte Carlo
(`N=50`, `alpha=0.1`, 20000 paths, stakes as in the repository; **toy, one onset position per row, not an
atlas run**):

| off state | onset `k` (post labels) | gate | P(promoted within 10 post labels) | within 30 |
|---|---|---|---|---|
| harmful 0.1 | 41 (10) | started mixture, all 50 starts x 5 stakes | 0.00 | - |
| harmful 0.1 | 41 (10) | trigger bettor `r=3` | 0.51 | - |
| harmful 0.1 | 21 (30) | started mixture, all 50 starts | 0.00 | 0.93 |
| harmful 0.1 | 21 (30) | trigger bettor `r=2 / 3` | 0.55 / 0.52 | 0.93 / 0.92 |
| neutral 0.5 | 21 (30) | started mixture, all 50 starts | 0.08 | 0.95 |
| neutral 0.5 | 21 (30) | trigger bettor `r=3` | 0.34 | 0.84 |

Null checks on the boundary iid law: started mixture 0.019, trigger bettor 0.076 (both at most 0.1;
the trigger bettor is closer to the level because it has no mixture slack). The neutral trigger
bettor also has pre-onset promotion probability 0.02 to 0.04, against about 0.001 for the mixture; it
is not a free improvement.

Reading, with caveats [H]: in the strong harmful cells the labels reveal the regime by themselves, so a
valid gate can use the **observed past as the onset detector** instead of paying `ln(#starts)`. The toy
bettor's stake is tuned to `q1 = 0.9` (a declared family effect, same status as the `R_valid` stake
prior), it ignores delay `d`, and it does not include the economic check or rollback. It is not a
candidate repair and was not evaluated on atlas cells; it only shows the multiplicity cost is not forced
by validity when pre-onset labels are informative. Whether anything *prior-free* achieves this is open.

## 5. Numeric comparison (from `scripts/check_onset_multiplicity_bound.py`)

`q0 = 0.55`, `q1 = 0.9`, `alpha = 0.1`, `K0 = 0.2928`, five repository stakes. Analytic requirement
`(ln(1/alpha) + ln #starts + ln #stakes)/g` where `g` = best grid-stake growth (ledger convention;
`episode_front`), `#starts = len(range(0, B, max(1, B//32)))`.

| `N=B` | #starts | analytic labels (started mixture) | proved lower bound, detection 0.9 (Thm 1, neutral ref.) | single-onset floor (m=1) | `ln(N/n_LB)` | `ln #starts` | Thm 2 expected-count bound |
|---|---|---|---|---|---|---|---|
| 50 | 50 | 26.8 | 9 | 4.65 | 1.71 | 3.91 | 3.27 |
| 100 | 34 | 25.5 | 11 | 4.65 | 2.21 | 3.53 | 4.00 |
| 250 | 36 | 25.6 | 13 | 4.65 | 2.96 | 3.58 | 4.92 |

Median-detection version (0.5): 5, 5, 6 labels.

Window-event probability bound at `N = 50` (Table C of the script), `beta(nK0; alpha/m)` with
`m = floor(N/n)`: `n=5`: 0.47; `n=10`: 0.85; `n>=15`: 1. Counting all 50 starts as `m` instead gives 0.34 and
0.58 at `n=5,10`; that would be invalid, since overlapping windows give `rho > 1`.

Ledger onset-0.8 cells: about 10 labels post-onset at `B=50` against an analytic 26 to 29. The bound says no
gate can reach detection probability 0.9 within about 9 post-onset labels *even in the neutral case*, and
that mean window-event probability within 10 labels is at most 0.85 (neutral reference). So the
10-label shortage is partly a hard limit: roughly `9` of the `26.8` needed labels
(and the `ln(1/alpha)/K0 = 7.9` known-onset part is included in the 9). The ledger observed
`diag_oracle_known_both` promotes in 0.71 of seeds in the `B=50` onset-0.8 cell, which is below the
neutral-reference ceiling and consistent with it. These cells are harmful-off, so Section 4 limits how far the
neutral-reference ceiling applies.

Cost accounting in nats (`B=50`): started mixture 7.82 = 2.30 (`ln 1/alpha`) + 3.91 (`ln 50`) +
1.61 (`ln 5`). Provable unavoidable pieces in the **neutral** case: 2.30 (`alpha`, known-onset) plus 1.71
(onset multiplicity at the bound's own `n`). Not covered: stake complexity (below). In harmful-off cells:
only the 2.30 known-onset piece is provable.

Stake complexity [H]. The bound assumes `q1` known, so stakes enter nowhere. For unknown effect size the
standard parametric price is about `(1/2) ln n` (Rissanen-type, universal coding) [H, not proved
here]; for `n = 26` this is 1.63 nats, about `ln 5 = 1.61`. If this holds, the stake grid is not
wasteful. Treat it as unproved.

Start-grid thinning [H, simple model, not simulated for the gate]. Model
`labels ~ (ln(1/alpha) + ln(N/D) + ln 5)/g + (D-1)/2` for start spacing `D`: minimised at `D = 7` for all
three budgets, giving 23.0, 25.4 and 28.6 against 26.8, 29.1 and 32.3 for `D = 1`, a saving of about 3.7
labels. The model ignores that early starts cost wealth and that the grid in the repository is already
`B//32`, so its `N=100, 250` row of 25.5 and 25.6 in the ledger is computed with 34 and 36 starts, not 100 and
250. The Monte Carlo above shows no benefit from spacing 7 over 1 (0.58 vs 0.62 at 20 post labels),
so this is a modest, unproven effect.

## 6. Source audit and R2 kill rule

I could read abstracts and parts of the HTML for items 1 and 2 below. Items marked "not retrieved" are
cited from secondary descriptions and are **not verified** against the text.

1. **Huang and Veeravalli, "Finite-Horizon Quickest Change Detection Balancing Latency with False Alarm
   Probability", arXiv:2511.12803 (2025). HTML read (statement fields), proof only summarised.**
   Setting: independent observations, one change `f0 -> f1`, `K = log E_{f1}[f1/f0] > KL(f1||f0)`.
   Constraint `P_inf(tau <= T) <= delta_F`; latency `ell` = smallest `d` with `P_nu(tau >= nu+d) <= delta_D`
   for all `nu` in `[m+1, T-d]`.
   **Theorem 1:** as `T -> infinity`, `ell >= (1/K + o(1)) [log T + log(1/delta_F) + log(1-delta_F-delta_D) + o(1)]`.
   The proof splits `{tau >= nu+ell}` by the log-likelihood-ratio level, uses a change of measure to `P_inf`, and a
   lemma that some onset has window null mass at most `delta_F/floor(T/ell)` (the packing step of
   Theorem 1 above). **Implies our bound in the neutral case, asymptotically.** Our finite-sample form
   with `KL(q1||q0)` and binary-KL is the non-asymptotic version already derived in
   `docs/switching_finite_horizon_qcd_budget_delay_audit_v1.md` (disjoint windows, adaptive chain rule,
   `kl_Ber(1-delta_F-delta_D || delta_F/M)`). It does not cover a harmful off state (their pre-change density
   is the null) or a composite null. TVT-CuSum and TVT-SR (Theorem 2) attain `O(log T)`.
2. **Bhattacharyya and Ramdas, "Change detection with conformal martingales: new optimal constructions, and
   suboptimality of existing methods", arXiv:2609.27179 (23 Sep 2026). Abstract and the section on
   restricted PFA minimaxity read.** **Theorem 3.9, Part 1:** for an iid simple pair with
   `0 < D = KL(P1||P0) < infinity` and late change points `I_N(kappa) = {ceil(kappa N), ..., N}`,
   `liminf_{N->inf} d_N*(alpha, delta, kappa) / log N >= 1/D`, for non-randomised and randomised stopping times
   under PFA control. Part 2: attainability by e-detectors with near-harmonic weights, `d_N*/log N -> 1/D`.
   The abstract also shows conformal/ARL methods can be `Omega(T)` or `Omega(sqrt(ARL))`. This states the
   `log(#change points)/KL` scaling directly (it is the same bound in the same direction, asymptotic in
   `N`, with no explicit `log(1/alpha)` term in the visible statement). Their proof of Part 1 was not
   visible in what I read. Also relevant: **Proposition 3.1** (no universal consistency for a fixed change
   point against a convex class) is the structural reason a composite null makes pre-change data
   uninformative for the gate. **Implies the neutral bound at the leading `log N` order.**
3. **Lai (1998), "Information bounds and quick detection of parameter changes in stochastic systems",
   IEEE Trans. Inf. Theory 44(7), 2917-2929. Not retrieved; secondary descriptions only.** Described as giving
   an asymptotic lower bound on worst-case expected delay under an ARL constraint, the lower bound `~ log gamma / I`
   with `I = KL`, and a window-limited false-alarm formulation (Section II.B) whose proof technique later papers
   reuse. The present multi-onset packing argument is the same family of technique. I cannot give the
   theorem number or exact constants from the text.
4. **Shin, Ramdas and Rinaldo, "E-detectors: a nonparametric framework for sequential change detection",
   arXiv:2203.03532 (2022), NEJSDS 2023. Abstract-level only.** E-CUSUM / e-SR control the **ARL** nonasymptotically
   (Theorem 2.4 per package docs) and give delay upper bounds in sub-Gaussian / sub-exponential families. They are
   upper-bound results; no PFA multiplicity lower bound found in what I read. Not a lower bound source, and
   the log-start-weight cost in e-detectors is exactly the algorithmic side of the question.
5. **Tartakovsky (book, "Sequential Change Detection and Hypothesis Testing", and Tartakovsky,
   Nikiforov and Basseville 2014). Not retrieved.** From general knowledge [H, unverified]: the PFA-constrained
   (Shiryaev, Lorden-Pollak, Lai) problem has first-order asymptotic optimality results with `log(1/alpha)/I`,
   and `log(gamma)/I` under ARL. A finite-horizon any-false-alarm constraint with exact multiplicity is addressed in
   source 1.
6. **Repository audits.** `switching_finite_horizon_qcd_budget_delay_audit_v1.md` contains the packing proof
   (`M = floor(T/ell)` windows, adaptive chain rule, binary data processing) and states it is not a new
   information inequality; `switching_unknown_onset_mixture_lower_bound_v1.md` records that convexifying onset
   alternatives did not sharpen a regret bound.

**R2 verdict: KILLED as a novelty claim.** Sources 1 and 2 state the leading-order result (`log T / KL` and
`log N / KL` latency under finite-horizon PFA), and the repository already holds the finite-sample window-packing
form. My contribution here is bookkeeping only: the overlap factor `rho`, the weighted-prior (min-entropy)
form, the pre-onset penalty for a harmful off state with its failure example, and the nats accounting against the
atlas gates. None should be presented as new.

## 7. Implication for Failure Atlas family 1

Family 1 is **strong effect with a harmful off state** (`q_off = 0.1`, `q1 = 0.9`, `alpha = 0.1`, `B` = 50 to 250
labels). Shares from ledger section 4 (per-round cost): onset 0.011 to 0.099, stake 0.001 to 0.058, residual
0.034 to 0.072.

* **Residual (label count / information)** [R for the known-onset part, otherwise H]. The known-onset floor
  (4.65 labels for detection 0.9; 7.9 on the growth heuristic) holds for any valid gate on `N_cond`, with any
  `q_off <= q0`. In onset-0.8 cells (about 10 post labels) the valid-gate ceiling is real: this is unavoidable
  cost of validity, as the reviewer assessment guessed. But it is only a **partial** account of the 26 to 29 labels.
  The analytic requirement includes the onset and stake terms, which are not unavoidable (below).
* **Onset share** [mixed].
  * Neutral-like off: provably unavoidable `ln(N/n)` of the `ln(#starts)` term, which is 1.7 of 3.9 nats at
    `B = 50`, 2.2 of 3.5 at 100, 3.0 of 3.6 at 250. So roughly 40 to 80 percent of the start-mixture
    onset penalty cannot be removed by any valid gate in the neutral case. The remaining 20 to 60 percent
    is start-grid algorithmic slack (thinning to spacing near `2/g ~ 7` labels) [H].
  * **Harmful off (all twelve ledger cells): no part of the onset share is proved unavoidable.** The packing bound
    is vacuous there (Section 4). The toy trigger bettor reaches 0.5 detection within 10 post labels where the
    started mixture reaches 0.0 (same `N`, `alpha`, stakes), at the cost of having validity but no mixture slack.
    So in these cells the onset share is **algorithmic headroom** for gates that use the informative observed past
    (history-dependent predictable stakes). This is a classical device (predictable betting), not a new
    mechanism; if used it must be reported as a baseline, and it must be tested on atlas cells under the
    locked criteria, with the economic check, rollback and delay `d`.
* **Stake share** [H]. Not covered by Theorem 1. Under the Rissanen heuristic (`(1/2) ln n ~ 1.6` nats) the
  five-stake grid costs about what is unavoidable for an unknown effect size. A family-declared effect level
  (`R_valid`) removes it by prior knowledge, which the protocol already classes as `prior_gap`, not a
  repair.
* **Net statement for the protocol.** (i) The reviewer's claim that the onset share "is expected to be
  unavoidable under a false-promotion constraint" is **supported only for neutral-like off states, and only
  for the `ln(N/n)` part, not `ln(#starts)`**. (ii) For harmful-off family 1 it is **not supported**: the
  harmful off state makes the gap partly closable by a valid gate that conditions on observed history, so
  `cost_of_validity` classification of the onset share would be wrong there. (iii) Cells whose shortfall is
  the post-onset label count alone remain `cost_of_validity`.

**Suggested follow-ups (not done, not authorised here).** (a) Add a history-triggered predictable bettor (and a
thinned start grid) as an `R_valid` variant and as a baseline for family 1, then re-evaluate `cost_of_validity` vs
`shared_failure`. (b) Prove or refute a common-null bound for the harmful composite case (needs a better
reference than `Bern(q')`, e.g. an adaptive null; I did not find one). (c) Have the theorem reviewed before it is
cited anywhere, as Amendment 2 requires.

## 8. Reproduction

    python scripts/check_onset_multiplicity_bound.py --paths 20000 --seed 1

Part A is deterministic. Part B Monte Carlo uses seeds `seed`, `seed+1`, `seed+2` for the validity,
started-mixture and trigger-bettor rows. Code: numpy only; `ruff check` passes. Limitations: Part B uses one
onset position per row and independent labels with no delay or economic layer; the bound is not tight in the
neutral case (Table C: 0.85 bound against 0.09 to 0.24 observed at 10 post labels).

## Reviewer note (2026-10-30, Opus review)

- **The "stop at the first 1 after r zeros" counterexample is too strong as stated.** It is valid
  only against the simple null Bern(q0). The project null is the composite conditional null,
  `E[-D_t | F_{t-1}] <= h`, and that null contains the harmful off state itself (for example
  Bern(0.1) for the favourable indicator). Under that member, the rule fires almost surely within
  N labels. So it does not show that a valid gate exists under the project null.
- **The toy history-triggered Kelly bettor is valid under the composite null.** Its stake is
  predictable and lies in [0, 1), so `1 + lambda_t (X_t - q0)/bound` is a supermartingale factor
  for every null member. Its 51% versus 0% detection result therefore stands as evidence of
  algorithmic headroom in the harmful-off cells. It is still a toy: it ignores delay, the
  economic check and rollback.
- **The packing bound with `q' = q_off` is the relevant one for harmful-off cells.** It gives only
  n >= 3, so the bound does not establish that the family-1 onset share is unavoidable. This is
  accepted. The ledger's section-7 reading ("onset share is close to the multiplicity penalty and
  expected unavoidable") is corrected: it applies to neutral-like off states only.
- **Novelty.** None is claimed. The bound is classical (R2).
