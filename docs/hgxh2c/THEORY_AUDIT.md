# HG x H2c theory audit (Amendment A1.7, written before any stage-3/4 result)

Status: proof and code audit of `src/shiftlab/hgxh2c/engines.py` and `grammar.py` as they stand in the working tree on 2026-10-31. Nothing here is a result. Two numerical checks (Section 6) are smoke checks, not proofs. No code was edited. Statements marked CODE-VERIFIED were checked against the lines cited; statements marked PROOF are derived below.

## 0. Setting, filtration, nulls

Event index n = 1..T. At event n the world produces latent quantities (B_n, C_n, h^B_n, h^C_n, d_n, U_n) with B_n, C_n in [0,1], proxies h^R_n in [0, pmax] (pmax = 0.6), `theta_R` the design constant, U_n a uniform on [0,1] that is independent of everything else (tape contract, `tapes.py`).

Full-data filtration. H_n = sigma( (B_s, C_s, h^B_s, h^C_s, d_s, U_s) for s <= n ). H_{n-1}-measurable means "a function of everything about events 1..n-1, including unreleased labels and the delays of earlier events". This filtration is larger than what the monitor sees. That is deliberate: a supermartingale with respect to a larger filtration is a supermartingale with respect to the monitor's own filtration (tower property; the wealth is adapted to the smaller one). The price is that the null must be stated on the larger one.

Per-track conditional nulls (PROTOCOL section 2), made precise:

- H0^B: E[B_n | H_{n-1}] <= theta_B for all n.
- H0^C: E[C_n | H_{n-1}] <= theta_C for all n.
- H0^J: H0^B and H0^C.

Two points that the protocol text leaves implicit and that matter.

1. The conditioning sigma-field is the JOINT history. Transfer operators let the C-history change B's stake (and vice versa). Validity therefore needs E[B_n | H_{n-1}] <= theta_B where H contains C's past. The weaker own-filtration null E[B_n | F^B_{n-1}] <= theta_B does not imply it. A world in which C_{n-1} predicts a B exceedance while B's own-history mean stays at or below theta_B violates H0^B in this sense, and a cross-stake can legitimately profit from that. The synthetic null families (iid copula noise, constant means) satisfy the joint null. `null_ar` does not satisfy it (the conditional mean moves; see Section 5).
2. The null is on the conditional mean of the raw bounded loss in normalised units. For C this is the affine-normalised cost clipped to [0,1] (`tapes.py`: B, C are built in [0,1] directly). If a real-data C was clipped, the null is about the clipped variable.

Delay and the event-indexed process. For event n the monitor forms the factor f_n = 1 + lam_n x_n (below). The wealth the monitor displays at calendar time tau is a product over a set of events that have been released by tau. The proofs work on the event-indexed product M_n = prod_{s<=n} f_s and then relate W_tau to M.

## 1. The factor form

For a betting track R in {B, C}, target of the candidate:

x_n = h_n + (Q_n / q_n)(R_n - h_n) - theta_R  (prediction-powered / Csillag form), `engines.py` loop path: `x = (eta*ht + (Qd/qs)*(Rt - eta*ht) - r0) * act`, with eta = 1 for every track the grammar builds (`corr="pp"`).
f_n = 1 + lam_n x_n, with `logf = torch.log1p(lam * x)`.

Quantities:

- q_n: the query probability actually used: `q = max(q_hook(q0), qfl).clamp(max=1)`, then zeroed if `spent >= budget`. Q_n = 1{U_n < q_n}.
- act_n = 1{q_n > 0}. When act_n = 0 the factor is exactly 1 (`lam = lam * act`, `x = (...) * act = 0`).
- lam_n: the stake, equal to min(max(hook(base stake), 0), hi) where hi = cap / Bd, cap = 0.5, Bd = pmax (1/q_floor - 1) + theta.

### Lemma 1 (surely positive factor) — PROOF, CODE-VERIFIED

Assume R_n >= 0, 0 <= h_n <= pmax, q_n >= q_floor on active events. On an active event x_n >= -Bd. Case Q=0: x = h - theta >= -theta >= -Bd. Case Q=1: x = h (1 - 1/q) + R/q - theta >= -h(1/q - 1) - theta >= -(pmax (1/q_floor - 1) + theta) = -Bd. So f_n >= 1 - lam_n Bd >= 1 - cap = 0.5 > 0 whenever lam_n <= cap/Bd. Inactive events have f = 1. QED.

Where the code enforces lam <= hi: after every stake hook, for every base other than grapa/grapa_grid (`engines.py`, `if tr.base not in ("grapa","grapa_grid"): lam = torch.minimum(lam.clamp(min=0.0), s["hi"])`). Base `grapa` is covered separately in Section 3.4.

### Lemma 2 (conditional mean of the increment) — PROOF

Suppose lam_n is H_{n-1}-measurable and q_n is measurable with respect to H_{n-1} and (h_n, d_n-free) free information of event n, i.e. sigma(H_{n-1}, h^B_n, h^C_n). Then, because U_n is independent of (R_n, h_n, H_{n-1}),
E[Q_n/q_n | H_{n-1}, h_n, R_n] = 1 on the event {q_n > 0}.
Hence E[x_n | H_{n-1}, h_n] = E[R_n | H_{n-1}, h_n] - theta, and by the tower property E[x_n | H_{n-1}] = E[R_n | H_{n-1}] - theta <= 0 under the track's null. Then E[f_n | H_{n-1}] = 1 + lam_n E[x_n | H_{n-1}] <= 1.

Two consequences used repeatedly.

- q_n may depend on the current free proxy h_n (the `ipw` query operator does, via `ctx.h`). This is harmless for the mean of x_n because the tower step integrates h_n out. It is NOT harmless for the stake: if lam_n depended on h_n, one would need the stronger conditional null E[R_n | H_{n-1}, h_n] <= theta. That is exactly the context-cap falsification recorded in `00_ANCHOR_SPEC.md` (section 0, finite-support counterexample, E[factor] up to 1.13). So the typing rule must forbid `h` in stake operators. Currently `PREDICTABLE` contains "h" for all channels (Section 7, fix F2).
- Inactive events (budget spent, q = 0) contribute factor 1. The pathwise budget (`spent >= budget` is determined by Q_1..Q_{n-1}) is therefore a predictable truncation of the active set. It cannot bias anything.

### Theorem A (per-track supermartingale) — PROOF

Fix a candidate whose stake lam_n and query probability q_n are of the form allowed by Lemma 2 (checked operator by operator in Section 3). Under H0^R, M_n = prod_{s<=n} f_s is a nonnegative supermartingale with respect to (H_n), M_0 = 1: nonnegative by Lemma 1, E[M_n | H_{n-1}] = M_{n-1} E[f_n | H_{n-1}] <= M_{n-1} by Lemma 2. Ville's inequality: P(exists n: M_n >= 1/alpha) <= alpha.

Relation to the displayed wealth W_tau:

- `release="prefix"` (the default of `Monitor`, used by `compile_batch`). Queried event s arrives at s + d_s, unqueried at s. The factor of event s is released at rel_s = max_{m<=s} arr_m (running max), so rel is nondecreasing and the set released by tau is the prefix {s <= N(tau)}, N(tau) = max{s : rel_s <= tau}. Hence W_tau = M_{N(tau)} and sup_tau W_tau <= sup_n M_n. The bound holds for ANY delay mechanism, including outcome-dependent delays, provided (i) the delays of earlier events are inside H_{n-1} and the null is conditional on them, and (ii) d_n is not used by lam_n or q_n (it is not: stakes use arrivals <= n-1, which depend only on events < n). The delay of event n only moves its release time.
- `release="legacy"` (every event arrives at s + d_s, no running max). The released set is {s : s + d_s <= tau}, not a prefix. For a CONSTANT delay d this is the prefix {s <= tau - d}, so the argument above holds. For delays that vary but are independent of the whole outcome process, condition on the delay sequence and reorder by arrival: the factor of s is multiplied in after factors of later-index events u > s with u + d_u < s + d_s, so the proof needs E[x_s | H_{s-1}, outcomes of those later events] <= 0. That holds for independent outcomes, not for general martingale-difference outcomes. For outcome-dependent delays nothing holds. Legacy is therefore VALID_UNDER_fixed_delay_or_independent_outcomes_and_delays. The grammar and stage 3 use prefix only (`compile_batch` never passes `release`); legacy exists for baselines.

Stakes at issue time. lam_n is computed at step n from state that has absorbed arrivals <= n-1 (`ring.pop("m_"+n, tt-1)`), from the displayed log-wealth at the end of step n-1 (`ctx.logW`, updated after all hooks at the end of step), from `spent` (before this step's Q is added), from free proxies (query operators only), and from design constants. Every one of these is a function of events 1..n-1 and the delays of those events, hence H_{n-1}-measurable. CODE-VERIFIED order inside `step`: absorb -> base stakes -> query hook -> Q drawn -> stake hooks -> factor -> release. The only quantity computed after Q_n is the factor itself. `ctx.logW` is rebound only at the end of the step (eager mode) or copied in place after all hooks (graph mode); no hook reads a value updated in the same step.

Delay and unobserved labels. A queried event whose label has not arrived has x_n not yet computable by the monitor, but f_n is still in M_n. The monitor only displays M_{N(tau)} where N(tau) counts released factors. Nothing in the proof requires the monitor to know x_n at issue.

Common query across tracks. One Q_n is drawn per event and used for both channels. Lemma 2 needs only U_n independent of (B_n, C_n, proxies, H_{n-1}). Correlated B and C do not matter for Theorem A, only for Section 4.

## 2. Boundedness and calibration assumptions

Theorem A needs: R in [0,1] (indeed only R >= 0 for positivity; the upper bound enters the efficiency but not validity because Bd is built on pmax, not on R_max); proxies in [0, pmax]; a design-time q_floor > 0 enforced by `torch.maximum(q, qfl)`; the nominal theta known and fixed before the stream (here `calibrate()` uses a separate seed stream, Monte-Carlo error of order 1e-3 in theta, treated as exact: this is an assumption, a theta that is 1e-3 too low inflates the null drift and should be examined by the `null_boundary` family).

## 3. Operator by operator (b)

Notation: for target track tgt and source src; `ctx.*` are the hook-visible quantities. Reads are copied from `grammar.OPS`.

### 3.1 S (stake) channel

All S operators return a stake that is then clamped to [0, hi] by the engine (not for grapa; Section 3.4).

- `ratio` (a, ref): lam' = (1-a) lam + a g, with g = own clipped Kelly (ref=1) or `base[guide] * bd[guide] / bd[tgt]` (ref=0). Reads base, kelly, bd, hi: released-moment functions. Predictable; convex combination of nonnegative predictable stakes. With a = 1, ref = 0 and a constant guide ratio this is discounted Kelly (X1 equivalence). VALID.
- `shift` (a): lam' = lam + a hi base[src]/hi[src]. Predictable, nonnegative. Before clamping it can exceed hi; the clamp restores lam <= hi. VALID (for grapa see 3.4).
- `gate` (thr): lam' = lam 1{mean[guide] > thr}. `mean[guide]` is the discounted released mean of the source increment (guide track, `bet=False`). Predictable, indicator in [0,1]. VALID. Note this includes HG's sign gate.
- `temper` (c0): lam' = min(lam, hi (c0 + (1-c0) clamp(logW[src]/LOG_THR, 0, 1))). logW[src] = displayed log-wealth through n-1. Predictable. VALID.

Composition (depth 2, fixed order) is a composition of predictable maps followed by the clamp. VALID.

### 3.2 Q (query) channel

The query operators return q' which the engine floors at q_floor and caps at 1.

- `boost` (b): q' = q (1 + b u), u = clamp(logW[src]/LOG_THR). Predictable, multiplier >= 1. VALID.
- `straddle` (m, lo): q' = m q when lo <= logW[src] < LOG_THR. Predictable, multiplier >= 1. VALID.
- `ipw` (e): q' = q (res_scale(src, h[src]) / sqrt(vbar))^e, a Xu-style variance-proportional allocation using the RELEASED residual second moments per proxy bin (predictable) and the CURRENT free proxy h[src] (free at issue). By Lemma 2 this is valid: q depends on h_n but the stake does not. The floor for candidates using `ipw` or `pace` is q_floor = 0.5 q0 (grammar `low`), so Bd is computed with the lower floor, and Lemma 1 holds. VALID_UNDER the condition that the stake never reads `h` (true today).
- `pace` (e, k): ratio of remaining budget per remaining step to the design rate, clamped to [0.5, 2], times (0.5 + k u). Reads `spent`, `ctx.T`, `ctx.t`, logW: predictable and deterministic design constants. Product can be < 0.5: the floor clamp handles it. VALID.

Pathwise budget: if spent_{n-1} >= B then q_n := 0 and the event is inactive. Predictable. VALID.

Two tracks, one Q: the Q operators of both directions compose multiplicatively on the same q (loop in `query`). Still predictable.

### 3.3 R (restart) channel — critical item

What the code does (CODE-VERIFIED, `engines.py` absorb section and `grammar.restart`):

- `restart` (k): when the displayed log-wealth of the SOURCE crosses k upward (cur >= k and the previous value < k), the engine sets the target's stake-estimation state (c1, c2, cn, ONS cur, ONS a, GRAPA-grid cl) to zero / one. The target's wealth `logW` is NOT touched.
- `soft` (rho): at the source's upward crossing of 0.5, the same state is multiplied by rho (c1, c2, cn, cur) and `a` becomes 1 + (a-1) rho. Again `logW` is not touched.
- `gamma` (g): the discount used when absorbing arrivals is switched to g when logW[src] >= 1.0.

Because the wealth is still W = prod (1 + lam_n x_n), and these hooks change only the predictable stake lam_n (a function of the reset state and of released data up to n-1), Theorem A applies verbatim. Verdicts:

- `restart`: VALID. It is a predictable stake-estimator restart, not a wealth restart.
- `soft` with keep fraction rho: VALID as implemented. Scaling c1, c2, cn by rho is a deterministic predictable map of the stake state; the Kelly ratio max(c1/(cn+1), 0)/(c2/(cn+1)) is then recomputed. For GRAPA-grid state scaling by rho > 0 does not change the argmax, rho = 0 sends it to the first grid point; both are predictable.
- `gamma`: VALID. The discount is a function of logW[src] through n-1 and is applied to the state accumulated before n.
- `gamma` on an ONS target: no effect (ONS has no discounted moments); `canonicalise` rejects it as `EQUIVALENT_TO:identity`. CODE-VERIFIED.

Mismatch to flag in the protocol text. PROTOCOL section 6 says restart mixtures are "sum of start-time-indexed e-processes with fixed prior weights". The code does not implement any start-time mixture. The R channel is a stake-estimator reset with a single wealth product. The validity proof is simpler than the one advertised, but the mechanism is also weaker than a change-point mixture: after a drawdown the wealth must climb from its current level, a restart does not give a fresh unit of capital. Any claim about "restart mixture" or "e-detector" behaviour must not be made about this implementation (NOVELTY_AUDIT.md section 6).

What would be INVALID (a wealth-level soft restart), analysed because the name invites it. Suppose at a data-dependent time tau one replaced the wealth by W' = rho W_tau + (1 - rho) and continued with the same factors. Then W'_t = rho M_t + (1-rho) M_t / M_tau after tau. If M_{tau-1} < 1 the jump E[W'_tau | H_{tau-1}] = rho E[M_tau|H_{tau-1}] + 1 - rho can exceed M_{tau-1} (e.g. M_{tau-1} = 0.5, rho = 0.5 gives up to 0.75): the process is not a supermartingale and Ville fails. The mechanism is that the capital "1 - rho" is injected from nowhere. The valid version is a start-time mixture with a capital ledger: weights w_j that are H_{j-1}-measurable (adaptive is fine), with sum_j w_j <= 1 pathwise, wealth W_t = sum_{j<=t} w_j prod_{s=j+1}^t f_s + (1 - sum_{j<=t} w_j). Conservation of capital gives E[W_t | H_{t-1}] <= W_{t-1}. A restart operator at the wealth level is allowed only in this form (typing restriction T-R below). The engine has no such operator today.

### 3.4 Base engines

- Kelly (discounted): lam = min(max(m1,0)/m2, hi) from released moments. VALID.
- ONS: `cur` updated from released z = x/(1 + lam0 x) and clipped to [0, hi]. The ONS recursion uses the base stake `lam0`, not the hook-modified stake; this is a design choice about what the ONS tracks, and it keeps the applied stake predictable. VALID.
- GRAPA (approximate, `base="grapa"`). The engine does not apply the `min(., hi)` clamp for grapa bases (`if tr.base not in ("grapa","grapa_grid")`). Without hooks the stake is bet/(2 bx) with bet in [0,1] and bx = max(Bd, 1/q_floor) >= Bd, so lam Bd <= 1/2 and Lemma 1 holds. With S hooks:
  - `ratio` and `gate`, `temper`: lam' <= max(lam, g) with g Bd <= 0.5 (guide track is Kelly, clipped to hi), so lam' Bd <= 0.5. Fine.
  - `shift` adds a hi base[src]/hi[src] with a <= 0.3; base[src]/hi[src] <= 1 for Kelly/ONS/grapa sources, so lam' Bd <= 0.5 + 0.15. Factor >= 0.35 > 0. Fine.
  - Depth 2 `ratio` then `shift`: still <= 0.65 / Bd. Fine.
  So positivity holds for every typed combination, but only by this margin argument, not by a clamp. It would fail for `grapa_grid` (grid up to 1.9, lam Bd up to 0.95) combined with any `shift` with a >= 0.1; `grapa_grid` is not in the grammar `BASES`, so it is not reachable. Verdict: VALID_UNDER the typed ranges (a <= 0.3, `BASES` without grapa_grid). Fix F3: clamp grapa stakes at the end to [0, 0.95/Bd] so the proof does not rely on parameter ranges.
- The grammar's guide tracks (`gB`, `gC`, `bet=False`) have no wealth and enter only through predictable moment state. VALID.

## 4. J combiners (c)

Let W^B, W^C be the two per-track wealth processes of Theorem A, both with respect to the SAME filtration H, started at 1.

### 4.1 Bonferroni (`bonf`): `lJ = max(lB, lC) - log 2` — VALID

Alarm iff max(W^B, W^C) >= 2/alpha. Under H0^J, P(sup W^B >= 2/alpha) <= alpha/2 and the same for C by Ville with threshold 2/alpha; union bound gives <= alpha. No dependence between B and C is needed. CODE-VERIFIED in both the fast path and loop path.

### 4.2 Fixed mixture (`mix`, w in {0.25, 0.5, 0.75}): `lJ = logaddexp(log w + lB, log(1-w) + lC)` — VALID

W^J = w W^B + (1-w) W^C is a convex combination of nonnegative supermartingales with fixed weights, hence a nonnegative supermartingale started at 1 under H0^J. Ville at 1/alpha. Weights are fixed before the stream (`typing` enforces w in the grid). Note it needs both tracks on a common filtration but nothing about their joint law. Remark: the mixture alarms on W^J >= 1/alpha, which requires one track to exceed 1/(alpha w), so it is less sensitive than `bonf` to a one-track harm and the weights are fixed design choices, not adaptive.

### 4.3 Product (`prod`): `lJ = lB + lC` — INVALID in general

W^J_t = W^B_t W^C_t. Both factors at step t use the same event, so
E[(1 + a X^B)(1 + b X^C) | H_{t-1}] = 1 + a E[X^B | .] + b E[X^C | .] + a b E[X^B X^C | .].
Under H0^J the first-order terms are <= 0 but the cross-term a b E[X^B X^C | H_{t-1}] has no sign restriction, and in this programme it is positive: B and C are generated with a Gaussian copula of correlation RHO = 0.5 (`tapes.py`), measured correlation of centred increments 0.483 in the check below, and in a real system both losses are driven by the same outcome. E[f^B f^C] = 1 + ab Cov(X^B, X^C) > 1 at equality of the null means. So W^J is a SUBmartingale in the null and Ville's bound does not apply.

Explicit counterexample (exact). X^B = X^C = epsilon_t Rademacher, a = b = 1/2. Each factor satisfies the null (mean 0). f = (1 + epsilon/2)^2 takes the values 2.25 and 0.25 with probability 1/2 each, E f = 1.25. The Lundberg exponent kappa solving E f^kappa = 1 is kappa = 1/2 (since (2.25^{1/2} + 0.25^{1/2})/2 = 1), so P(sup W >= 1/alpha) is of order alpha^{1/2}, not alpha. Monte Carlo (Section 6): P(sup_t W_t >= 20) = 0.185 at T = 2000 against 0.0377 for a single factor.

Does "same filtration with sequential betting" repair it? Interleaving the factors within a step: make the C-factor's stake H_{t-1} ∨ sigma(X^B_t)-measurable. Then E[f^B f^C | H_{t-1}] = E[f^B (1 + b E[X^C | H_{t-1}, X^B_t])]. This requires the CONTEMPORANEOUS conditional null E[C_t | H_{t-1}, B_t] <= theta_C, which is stronger than H0^C and is false whenever B_t and C_t are dependent with E[C_t | B_t] non-constant (the case here). So within-step interleaving does not rescue it.

Valid fixes (any ONE):

- P-1 Time interleaving: the B-factor is applied at odd events and the C-factor at even events (the other track's increments still feed the stake state). Then each event carries a single factor and f_n is valid under the track's own null. Product validity then holds under H0^J. Costs half of each track's data for wealth growth.
- P-2 Linear (vector) factor: 1 + a X^B + b X^C with a, b >= 0 and a Bd_B + b Bd_C <= cap (the VectorMixMonitor / Ryu-Wornell form). Valid for any dependence under H0^J; it is NOT the product of the per-track wealths.
- P-3 Cross-term bound: use f = (1 + a X^B)(1 + b X^C) only with the product capped, f' = 1 + a X^B + b X^C + a b min(X^B X^C, 0) — this is <= the linear factor and so valid, but it gives up exactly the positive-correlation gain that the product was meant to exploit.
- P-4 Independence by construction: product is valid if X^B_t and X^C_t are conditionally independent given H_{t-1}. Not the case here and not checkable from the null alone.

Required typing change: the `prod` combiner must be rejected (UNTYPED:prod_not_valid_under_dependence) unless implemented as P-1, P-2 or P-3. Until then any candidate with `comb == "prod"` is INVALID for the intersection null and must not be a stage-4 finalist; it may remain in the search only as an empirical-alarm comparator and its Delta_J must be reported as such.

### 4.4 What the J guarantee does and does not cover

All three combiners above, when valid, control P(alarm) under H0^B AND H0^C. The protocol's J endpoint charges `c_FA * 1{alarm in a world where track-C's null holds}` (PROTOCOL section 7). In worlds such as `pred_only`, H0^C holds but H0^B fails, and a J alarm driven by the B track is charged as a false alarm although no theorem bounds it (the intersection null is false there). So the guarantee is size under the intersection null; the J-cost penalty is a decision-cost accounting choice on top. Report J false alarms in `pred_only` separately from FAR under H0^J.

## 5. Assumptions NOT covered (d)

1. Martingale-difference outcomes are assumed: E[R_n | H_{n-1}] <= theta. `null_ar` (AR(0.9) latent copula) has a conditional mean that moves with the past, so E[R_n | H_{n-1}] can exceed theta even though the marginal mean equals theta. No guarantee; reported as a stress result. The anchor documents AR(1) covariate nulls with FAR up to 0.17-0.36.
2. Joint-filtration null (Section 0, point 1). A cross-stake exploits information that the own-filtration null does not control.
3. Informative or look-ahead delays. Prefix release covers any delay mechanism only if the delay of event s does not carry information about future outcomes beyond what H_s holds. Delays that depend on outcomes of later events (e.g. a batching process driven by future labels) are not covered. The dev grid uses constant delays.
4. Outcome-dependent query policies. The typing allows q_n to depend on released data, free proxies, wealth and spending, never on the unobserved current outcome R_n or on Q's of the future. A query rule that peeks at R_n, or an adaptive q that uses h_n inside the stake, is outside the typing.
5. Misspecified theta. theta is an exact known constant. Estimated nominals (calibration-sample noise) are not covered; the anchor shows n_cal <= 1000 destroys power. The 1e-3 Monte-Carlo error in `calibrate()` is treated as zero.
6. Out-of-range data. R in [0,1], proxy in [0, 0.6]. A violated bound breaks Lemma 1.
7. Empirical-alarm baselines (CUSUM, Page-Hinkley, Shiryaev-Roberts with simulated thresholds) have no anytime-valid guarantee by construction.
8. Product combiner (Section 4.3) and legacy release under non-constant delays (Section 1).
9. Multiple finalists / selector: a deployed selection rule among candidates is a data-dependent choice of monitor; its validity needs a multiplicity argument (union over a fixed finite list, or a selector that depends only on design-time observables). PROTOCOL section 7 restricts the selector to design-time observables; with that restriction a pre-specified selector is a measurable choice of one valid monitor before the stream. If it used stream data, Bonferroni over the candidate list would be required.
10. Repeated use across time (an alarm followed by restart of monitoring): each monitoring run is a separate level-alpha test.

## 6. Numerical smoke checks (not proofs)

Run on 2026-10-31 with `.venv/Scripts/python.exe` on CPU; scripts are in the session scratchpad, no repository file was modified.

1. Rademacher counterexample (Section 4.3): P(sup W >= 20) = 0.1853 (product, a=b=0.5, T=2000, 20,000 paths) versus 0.0377 (one factor).
2. Engine, independent HG-style tracks (kelly gamma .99/.995, no transfer), null_stationary, d = 5, full labels, 1500 audit seeds, T = 2000. Measured corr(B-theta_B, C-theta_C) = 0.483.

| combiner | J FAR | B FAR | C FAR |
|---|---|---|---|
| bonf | 0.037 | 0.038 | 0.032 |
| mix w=0.5 | 0.040 | 0.038 | 0.032 |
| prod | 0.091 | 0.038 | 0.032 |

The product combiner exceeds alpha = 0.05 (137/1500, Clopper-Pearson lower bound about 0.077) while bonf and mix do not. With 20% labels all four are at or near zero FAR (the null is conservative there); null_boundary is conservative for all combiners. This confirms the theoretical conclusion for the product combiner under the registered null family.

3. Operator smoke screen: each typed operator once in each direction (BC and CB), one representative parameter, base kelly/kelly, combiner bonf, null_stationary, d = 5, full labels, 400 audit seeds, T = 2000 (22 candidates; `ratio` with ref=1 was rejected by canonicalise as discounted Kelly). Per-track FAR ranged 2/400 to 20/400 (maximum: BC `shift`, C track, 20/400 = 0.050, i.e. at alpha with a wide interval); the J (bonf) FAR ranged 4/400 to 13/400 (maximum 0.033). No NaN. Every candidate is consistent with FAR <= 0.05 at this sample size; this is a bug screen, not evidence of validity, and sample size is too small to detect FAR excess below about 0.03. The ONS/grapa bases, the 20% label regime and null_boundary were planned (600 seeds) but not completed in the session time budget; the first run was stopped before output and is not reported.

## 7. Verdict table and required fixes

| Operator / component | Verdict |
|---|---|
| Per-track wealth, prefix release, any delay mechanism | VALID_UNDER joint-filtration martingale-difference null (conditional on delays of earlier events) |
| Per-track wealth, legacy release | VALID_UNDER constant delay (or delays independent of outcomes with independent outcomes); INVALID for outcome-dependent delay |
| S ratio guidance | VALID |
| S prior shift | VALID (grapa target: VALID_UNDER a <= 0.3, see F3) |
| S sign gate | VALID |
| S tempered cap | VALID |
| Q boost | VALID |
| Q straddle | VALID |
| Q variance-optimal IPW (`ipw`) | VALID_UNDER stake never reads current proxy h (F2) |
| Q shared pacing | VALID |
| Pathwise budget truncation | VALID |
| R restart on crossing | VALID (stake-estimator reset; wealth untouched) |
| R start-time component (`soft`, keep fraction rho) | VALID as implemented (moment-state scaling); a wealth-level version would be INVALID unless done as a capital-ledger start-time mixture |
| R gamma switch | VALID |
| Base Kelly, ONS | VALID |
| Base GRAPA (approx) | VALID_UNDER typed ranges (margin 0.35); F3 for a clamp |
| J Bonferroni | VALID (H0^J) |
| J fixed mixture | VALID (H0^J) |
| J product | INVALID in general (Section 4.3) |
| Empirical-alarm baselines (CUSUM, PH, SR with simulated threshold) | NO GUARANTEE |
| null_ar family | outside the guarantee |

Required code and typing fixes (none applied here; the engine is being used by the running pipeline):

- F1 `prod` combiner: reject in `grammar.typing` (`UNTYPED:prod_not_valid_under_dependence`) or reimplement as P-1 (time-interleaved factors) or P-2 (linear vector factor) or P-3. Remove `("prod", 0.0)` from `COMBS`, which changes the canonical space (denominator: 5 combiners to 4; blocks 45 to 36). Registered candidates already evaluated with `prod` stay in the registry with reason `INVALID_COMBINER` and are excluded from finalist selection.
- F2 Channel-specific read sets: replace the single `PREDICTABLE` set by `PREDICTABLE_S = {logW, mean, base, kelly, spent, hi, bd}` and `PREDICTABLE_Q = PREDICTABLE_S | {h, res}`, so `typing` rejects any S or R operator that reads `h` or `res`. No current operator violates this, but the rule as written would accept one.
- F3 Clamp stake of grapa bases after the hooks to [0, 0.95/Bd] (`engines.py`, both paths) so positivity does not depend on parameter ranges.
- F4 Document in PROTOCOL section 6 that the R channel resets stake-estimator state only, not the wealth, and that no start-time mixture is implemented. If a true start-time mixture is wanted, use the capital-ledger form of Section 3.3 (typing restriction T-R: w_j H_{j-1}-measurable, sum w_j <= 1).
- F5 State in every report that the validity statement is for the joint-filtration null and give null FAR with Clopper-Pearson intervals for `null_ar` as stress-only.
- F6 Add a unit test that draws 1e5 iid null paths on a toy tape (x with correlated B, C) and asserts, for each combiner, an upper Clopper-Pearson bound at 0.05 for bonf and mix and a documented failure for prod; and a finite-support exact test of E[f_n | H_{n-1}] <= 1 for each stake and query operator by enumeration (as `tests/gap/test_engine.py::test_exact_finite_support_cap` does for the cap).

## 8. Independent checking

The `proof-checker` skill was invoked on this document; see the record in Section 9.

## 9. proof-checker record

The `proof-checker` skill was invoked (Skill tool) on this document on 2026-10-31. Its required cross-model reviewer (Codex MCP, `gpt-6-astra`, effort ultra) is NOT available in this session: no `mcp__codex__*` tool is registered (ToolSearch found none). Per the skill's own rule this slot is `REVIEW_UNAVAILABLE`, and the acceptance gate cannot be marked PASS by cross-model review. No `PROOF_AUDIT.json` was produced (the skill writes it only with a reviewer thread). The following is an executor-side self-review against the skill's checklist; it is NOT an independent check and must be repeated with the reviewer when it is available.

Self-review findings (applied above or recorded as open):

1. HIDDEN_ASSUMPTION (fixed in text): Theorem A needs the delays of earlier events inside H_{n-1} and the null conditional on them; stated in Section 1 and item 3 of Section 5.
2. HIDDEN_ASSUMPTION (fixed in text): positivity needs R >= 0 and h in [0, pmax]; in Lemma 1 and Section 2.
3. CASE_INCOMPLETE (checked): inactive events (q = 0) have factor exactly 1; `proxy_only`/`eta`/`csillag`/`lrt` tracks are baselines outside the grammar and are not covered by Theorem A. Only `corr="pp"` tracks are.
4. UNJUSTIFIED (open): the Section 4.3 exponent argument gives P(sup W >= 1/alpha) of order alpha^{1/2} for the Rademacher example; the exact constant was checked by Monte Carlo only (0.185 vs 0.038). The qualitative claim (failure of Ville) is proved by E[f] = 1.25 > 1; the order claim is asymptotic (Lundberg).
5. UNJUSTIFIED (open): P-3 (capped cross-term) is asserted valid because it is pointwise <= the linear factor 1 + aX^B + bX^C; this needs a + b feasibility (a Bd_B + b Bd_C <= cap) and the linear factor being a supermartingale (a one-line proof: its conditional mean is 1 + aE X^B + bE X^C <= 1). Not an implemented operator.
6. SCOPE (open): the table entry "VALID" for ONS rests on Lemma 2 only through predictability of `cur`; the regret/power properties of ONS are not claimed.
7. UNCLEAR (open): graph-mode execution (`Monitor(graph=True)`) replays one captured step; this audit read the eager and fast paths. In-place state updates were checked by reading but not executed on a GPU. The fast path (no hooks) was read for the product and mixture combiners only.
8. Counterexample pass: product combiner (found, verified algebraically and numerically); context-dependent stake (known, anchor spec); wealth-level soft restart (found, algebraic: jump from M < 1); legacy release with non-constant delays and MDS outcomes (candidate, not constructed); grapa_grid with `shift` (candidate by arithmetic, not reachable in the grammar).
