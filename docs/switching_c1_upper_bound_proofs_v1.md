# C1-B upper bound: lemma-level proofs, the exact break points, and numerical constant checks

**Date:** 2026-10-30. **Status:** THEORY APPENDIX (development). Nothing here is a validated novelty claim and nothing was run on
repository data. Marks: **PROVED** = full proof given below; **PROVED-MODULO** = proof given modulo a named imported theorem;
**CONJECTURE** = not proved. Source rule: only the sources in `switching_c1_source_theorem_audit_v1.md` are named. Where a standard
inequality (Ville, Azuma, Freedman, Birkhoff contraction) is used without being in that audit it is flagged "needs source check" for
a formal citation; each such step that is load-bearing is proved inline instead.

Scratch scripts (outside the repo): `C:\Users\nigel\AppData\Local\Temp\claude\C--Users-nigel--claude-spares-spare-HQYN75\6eec0303-54f7-4457-a727-0b093e7dee97\scratchpad\c1b_check.py`
and `...\c1b_toyA.py`. Run `python c1b_check.py` (about 15 s, CPU) then `python c1b_toyA.py`.

## 0. Summary and where the sketch broke

| Item | Mark | One-line result |
|---|---|---|
| Lemma 0 (transcript posterior is the fixed-pattern posterior; delay enters only through the release clock) | PROVED | needs query decisions to be functions of released data only; violation counterexample given (posterior error 0.316 in an exact enumeration) |
| L1 sparse-observation forgetting | PROVED (self-contained) | `TV <= (1 - a_-/a_+)^(n-1)` for every observation pattern and every values, delay included; agrees with DMR Thm 6 / Prop 5 / Ex. 2 as recorded in the audit (not re-read) |
| L2 per-query information | PROVED for the **burst class only**; FALSE for arbitrary predictable policies | separation must be of an `m`-block, uniformly over start beliefs; per-query separation has explicit counterexamples |
| L3 LLR concentration | PROVED at the **1/kappa** rate (burst class, bounded log-ratios) | direct exponential-supermartingale argument via a variance-KL inequality; no dependent-McDiarmid needed; the 1/kappa^2 version is only a fallback |
| Theorem C1-B | PROVED-MODULO Ville's inequality and Theorem C1-A (theory-targets doc) | explicit `n*`, wall-clock `d + n*/q`, conditional on an observable "beneficial" event, not on latent regime onset |
| Tightness vs C1-C | statement PROVED; constants are loose | measured: proven `n*` is 14-38x the Monte Carlo 95% exclusion time and 280-950x the C1-C floor on the toy families |
| `E[S_n] >= n*kappa_rate - C_f` for a single long run, and the sharp (non-burst) constants | CONJECTURE | route sketched in 4.5 |

Corrections to `switching_theory_targets_c1_c2_v1.md` section 1.5 (these are genuine errors or gaps in the sketch, not wording):

1. **"Equivalent parameters give `mu_t(theta) = mu_t(theta*)`" is false at finite `t`.** Equivalence (equal stationary output laws)
   gives equal predictives only for stationary starts. With initial laws `nu_theta != nu_theta*` the predictive means differ by a forgetting
   term `<= 4 (1 - a_-/a_+)^(t-1)`. The theorem therefore needs a margin `gamma_0` and a burn-in `t_f` (Cor. 1.3). L1 is load-bearing here.
2. **Step 2 ("conditional KL at step `i` converges geometrically to `kappa_rate`") does not hold for an adaptive predictable policy.**
   The conditional KL of one query is `Psi_1(b*, b)`, a function of the two predictive beliefs, and it is **zero** at reachable belief pairs
   (Section 4.3: exactly zero at `b = 2/3` in Toy B). A pattern-tailored predictable policy can sit where it is arbitrarily small. The
   per-query rate is policy-dependent; no `kappa_rate` is common to all predictable policies. Fix: restrict to **bursts** of `m` consecutive
   queries and separate on the `m`-block, which is uniform over start beliefs (Prop. 4.2).
3. **The dependent-sequence McDiarmid route (step 3) is not needed and gives the weaker rate.** A Chernoff bound on the LLR with the
   self-bounding variance `E[l^2 | past] <= (2 + L) KL` gives the `1/kappa` rate directly (Prop. 5.3), so "C1-B+" is resolved for the burst class.
4. **DMOvH Thm 12 and Thm 14 are not used.** The positive-rate fact is replaced by an elementary finite-block statement (the first block length
   at which two stationary output laws differ), which also yields `liminf D_n/n >= kappa_0/m > 0` as a by-product.
5. **Promotion requires `theta* in C_t`**, so the success probability is `1 - alpha - delta`, not `1 - delta`.
6. **"Within `n*` queries after the regime becomes beneficial"** cannot be proved as worded. The parameter is fixed, so information about
   `theta` accrues independently of the latent regime. What is proved is: after `n*` released queries and `t >= t_f`, the gate promotes at
   every `t` at which the *observable* event `mu_t(theta*) > h + gamma_0` holds. The latent-onset-to-belief delay is a separate window problem (Section 8).

## 1. Setting, constants, assumptions

- **A1 (family).** `Theta` finite, `pi` a prior with `pi* := pi(theta*) > 0`. True parameter `theta*`.
- **A2 (strong mixing; the constants).** Hidden space `Z = {1..K}`. Every `A_theta` is stochastic with all entries in `[a_-, a_+]`, `0 < a_-`.
  Set `r := a_-/a_+`, `rho_F := 1 - r` (filter rate), `varrho := 1 - K a_-` (unconditional-chain rate). Since `a_+ >= 1/K`, `varrho <= rho_F`.
  Stationary law `pi_theta`; `R_theta := {b A_theta : b in simplex}` (one-step predictive beliefs; contains `pi_theta`).
- **A3 (bounded emissions).** Finite alphabet `Y subset [-1,1]`, `g_theta(y|z) in [g_-, g_+]`, `g_- > 0`, `L := log(g_+/g_-)`.
  Initial laws `nu_theta in R_theta` (e.g. stationary). Per-state mean `m_theta(z) = sum_y y g_theta(y|z) in [-1,1]`.
- **A4 (contract, as in the theory-targets doc 1.1).** Fixed delay `d >= 1`, pathwise cap `B` (pending included), horizon `T`; the query at event `s` is
  a function of the labels **released by time `s`** (events `<= s - d`), past query indicators, and private randomness `U` independent of `theta`
  and of the outcomes; querying does not affect outcomes. Gate and `mu_t(theta) = E_theta[X_t | O_t]` as registered.
- **Equivalence.** `theta ~ theta'` iff their stationary output processes have equal laws (equivalently equal `m`-block laws for all `m`).
  `[theta*]` is the class of `theta*`. For `theta in Theta` and `beta` a belief on `Z`, `P^theta_{beta,m}` is the law of `m` consecutive outputs when the
  first state has law `beta`; `S^theta_m := P^theta_{pi_theta,m}`.
- **A5 (burst class `Q_m(B)`).** The set of queried events is a union of **disjoint blocks of `m` consecutive events**; the start of each block is
  decided predictably (A4), and once started a block is never aborted. At most `floor(B/m)` blocks.
- **A6 (burst separation).** `kappa_0 := min_{theta in Theta_conf} min_{(b*, b) in R_theta* x R_theta} Psi_m(b*, b) > 0`, where
  `Psi_m(b*, b) := KL(P^{theta*}_{b*,m} || P^{theta}_{b,m})` and `Theta_conf` is defined next. Per-label separation: `kappa_sep := kappa_0/m`.
  (A6 holds for `m >= m_1 + r_0` by Prop. 4.2; it can also hold for much smaller `m`.)
- **Decision-equivalence (quotienting).** Fix a margin `gamma_0 > 0` and a burn-in `t_f` (Cor. 1.3). The **conflict set**
  `Theta_conf := { theta in Theta \ [theta*] : exists t in [t_f, T], exists an observation pattern/values o with positive probability, mu_t(theta|o) <= h and mu_t(theta*|o) >= h + gamma_0 }`.
  Parameters outside `[theta*] union Theta_conf` can never cause a false block of a beneficial promotion; they are quotiented out of A6. This is a finite check
  (finite alphabet, finite `T`) but the bad set is history-dependent, so `Theta_conf` is defined by existence, not by a clean parametric condition.
  `Theta_conf = Theta \ [theta*]` is the conservative choice.

## 2. Lemma 0: what the adaptive/delayed transcript does and does not change. PROVED

**Statement.** Let `O_t = (q_{1:t}, y_{R_t})` be the observable transcript at decision time `t` (all query indicators including pending ones, and the values of
released queried events `R_t = {e : q_e = 1, e + d <= t}`). Under A4, for every `theta`,

`P_theta(O_t = o, Z_t = z) = kappa(o) * Q_theta(X_{R_t} = y_{R_t}, Z_t = z)`,

where `kappa(o) = prod_{s<=t} kappa_s(q_s | H_s)` does not depend on `theta`, and `Q_theta(.)` is the HMM law with unreleased and unqueried coordinates summed out (missing).
Hence `P_theta(Z_t = z | O_t = o)` is the **fixed-pattern** HMM filter/predictive with the pattern `R_t` treated as given, and `L_t(theta) propto Q_theta(X_{R_t} = y_{R_t})`.

*Proof.* Condition on `U`. Each factor `kappa_s(q_s | H_s)` depends only on `(q_{<s}, y_e : e in R_{s}, e + d <= s)`. Every such `e` satisfies `e <= s - d <= t - d`, so `e in R_t`: the factor is a function of `o` only.
Writing `P_theta(o, z_t) = sum_{z_{1:t-1}, x_{1:t}} P_theta(z, x) prod_s kappa_s 1{x_e = y_e, e in R_t}` and pulling the `o`-measurable `kappa` factors out of the sum gives the display. Dividing by `P_theta(o)` cancels `kappa(o)`. QED.

**Consequences.**
(i) *Delay enters only through the release clock.* The LLR `S_j = sum_{i<=j} log p_{theta*}(Y_i | Y_{<i}) / p_theta(Y_i | Y_{<i})` is indexed by label order and contains no `d`. The gate uses `S_{j(t)}`, `j(t) = #{queried e : e <= t - d}`. Delay shifts the evaluation index and removes the last `d` labels from the policy's information; it does not slow per-label information.
(ii) *The query indices are predictable in label order.* `s_{j+1}` is a function of `(Y_{<=j}, U)`, because between `s_j` and `s_{j+1}` nothing new is queried, so every label the policy can have seen is among `Y_{<=j}`. The filtration `F_j = sigma(Y_{<=j}, U)` makes `l_j` a bounded increment with `E[l_j | F_{j-1}] = KL(p_{theta*}(.|Y_{<j}) || p_theta(.|Y_{<j})) >= 0`. Note this conditions on *all* earlier-index labels, including labels still pending at decision time; that is legitimate (it is a likelihood factorization, not the learner's information state).

**Necessity of the A4 restriction (counterexample, exact).** Policy: query event `s` iff `x_{s-1} = +1`, where `x_{s-1}` is unreleased when `d = 2`. In an exact enumeration (`T = 7`, `d = 2`, two-state HMM, all `2^7 * 2^7` paths, 46 transcripts) the true posterior of `Z_T` given the transcript differs from the fixed-pattern filter by up to **0.316**; for a legitimate released-data policy the maximum discrepancy is `2.2e-15` (12 transcripts). So when queries read unreleased data the "missing-at-random" reduction, the likelihood factorization of C1-A, and L1's use of a fixed pattern all fail together.

## 3. L1: sparse-observation forgetting under an arbitrary predictable pattern. PROVED

**Reduction.** By Lemma 0, the posterior given `O_t` is the HMM posterior with weights `w_k : Z -> [0, inf)`, `w_k(z) = g_theta(y_k | z)` if event `k` is released-observed and `w_k = 1` otherwise ("missing symbol": a likelihood-1 observation). Pending queried events and unqueried events are both `w_k = 1`. The *predictive* of `Z_t` is the filter at `t` with `w_t = 1`.

**Lemma 1.1 (L1).** Let `A` be stochastic with entries in `[a_-, a_+]`, `r = a_-/a_+`. Let `w_1..w_n` be any nonnegative weight functions and `mu, mu'` any two initial laws with positive total weight under both. Let `f^mu_n` be the law of `Z_n` given the weights (filter including `w_n`). Then

`TV(f^mu_n, f^{mu'}_n) <= (1 - r)^{n-1}`.

This holds for every weight sequence, hence for every observation pattern and every values, including all-missing.

*Proof.* Define backward functions `beta_n = 1`, `beta_k(z) = sum_{z'} A(z,z') w_{k+1}(z') beta_{k+1}(z')`. The posterior of `Z_{1:n}` is a (Doob-transformed) time-inhomogeneous Markov chain with initial law `w^mu(z) propto mu(z) w_1(z) beta_1(z)` and kernels
`F_k(z, z') = A(z,z') h_{k+1}(z') / sum_{z''} A(z,z'') h_{k+1}(z'')`, `h_{k+1} := w_{k+1} beta_{k+1}`, `k = 1..n-1`. The kernels depend on `(A, w)` only, **not** on `mu`. Hence `f^mu_n = w^mu F_1 ... F_{n-1}`.
Put `p_{k+1} = h_{k+1}/sum h_{k+1}`. Since `A(z, .) >= a_-` and `sum_{z''} A(z, z'') p_{k+1}(z'') <= a_+`, we get `F_k(z, z') >= r p_{k+1}(z')` for all `z`, i.e. `F_k = r 1 p_{k+1} + (1 - r) F~_k` with `F~_k` stochastic. Therefore `(nu - nu') F_k = (1 - r)(nu - nu') F~_k` and `TV` contracts by `(1 - r)` per kernel. Apply `n - 1` times and use `TV(w^mu, w^{mu'}) <= 1`. QED.

This is the DMR argument in the finite strong-mixing case: the audit records DMR Thm 6 with Prop 5 / Example 2 as giving ratio `1 - sigma_-/sigma_+`, and here `sigma_-/sigma_+ = a_-/a_+`; I did not re-read DMR, and the proof above does not depend on it. The "missing symbol" reduction needed no assumption on `g`; adaptivity of the pattern is harmless *because* of Lemma 0 plus the pathwise form of Lemma 1.1.

**Corollary 1.2 (predictive and LLR consequences).** With `P^{nu}` the law from initial belief `nu`:
(a) predictive state TV at event `s` for any pattern: `<= rho_F^{s-1}`;
(b) predictive label law: `|p^nu(y | history) - p^{nu'}(y | history)| <= rho_F^{s-1} (g_+ - g_-)`, so `|log p^nu / p^{nu'}| <= rho_F^{s-1} (e^L - 1)`;
(c) **initial-condition insensitivity of the LLR** (the pathwise `C_f` of the sketch): `|log L^nu(transcript) - log L^{nu'}(transcript)| <= (e^L - 1)/r` for any pattern, because labels have distinct event indices `s_j >= j` and `sum_j rho_F^{s_j - 1} <= 1/(1 - rho_F) = 1/r`. For an LLR between two parameters the bound doubles.
(d) **Delay vs persistence.** `|mu_t(theta|o) - mubar_theta| <= 2 varrho^d`, `mubar_theta := sum_z pi_theta(z) m_theta(z)`, because the predictive of `Z_t` is `(posterior at an event <= t-d) A^d` and `TV(b A^d, pi) <= varrho^d`. If `mubar_theta* + 2 varrho^d <= h + gamma_0` the beneficial event of Theorem C1-B can never occur (the model-conditional guarantee is silent; a better acquisition rule cannot repair this).

**Corollary 1.3 (equivalent parameters and the burn-in).** Let `theta' in [theta*]`. For every pattern/values `o`, `|mu_t(theta'|o) - mu_t(theta*|o)| <= 4 rho_F^{t-1}`.
*Proof.* Under *stationary* starts the conditional mean of `X_t` given the observed coordinates is a functional of the output-process law, identical for `theta'` and `theta*` (all `o` have positive probability by A3). Each actual start differs from its stationary start by TV `<= rho_F^{t-1}` on the state (Lemma 1.1 with the weight at `t` equal to 1), hence by `<= 2 rho_F^{t-1}` in the mean since `m in [-1,1]`. QED.
Define `t_f := 1 + ceil( log(4/gamma_0) / log(1/rho_F) )`. For `t >= t_f` and `mu_t(theta*) > h + gamma_0`, every `theta' in [theta*]` has `mu_t(theta') > h`.

**Does the adaptive pattern break anything?** No, provided Lemma 0 holds. Everything in L1 is pathwise in the pattern and values; the only place adaptivity could enter is the identification of the posterior, which Lemma 0 settles. **Numerics** (script section 1): exhaustive over all `3^n` patterns/values for `n <= 10` (missing, -1, +1), two extreme initial laws. Worst-case TV equals `0.8^(n-1)` exactly for the symmetric chain (`a_- = .1`, `a_+ = .9`), compared with the proven `(8/9)^(n-1)`; for the asymmetric chain `[[.9,.1],[.3,.7]]` worst TV at `n = 10` is 0.0156 vs bound 0.346. For the symmetric chain the true rate `0.8 = (1-r)/(1+r)` is the Birkhoff-type coefficient, so the proven rate is conservative by about a factor `(1+r)`; improving to `(1-r)/(1+r)` would need the Hilbert-metric contraction (**needs source check**; not used). LLR initial-condition insensitivity (script section 5): observed max 2.93 vs proven 72.

## 4. L2: per-query information

### 4.1 What can and cannot be asked

Write `Psi_m(b*, b) = KL(P^{theta*}_{b*,m} || P^theta_{b,m})`. For a block started at label index `j` the conditional law of the next `m` labels given `F_{j-1}` is `P^{theta*}_{b*_j, m}` with `b*_j = P_{theta*}(Z_{s_j} | Y_{<j})`, and under `theta` it is `P^theta_{b_j,m}` with `b_j = P_theta(Z_{s_j} | Y_{<j})` (Markov property of the hidden chain). Thus
`E_{theta*}[ sum_{i in block} l_i | F_{j-1} ] = Psi_m(b*_j, b_j)` **exactly**, and `b*_j, b_j in R` (for `s_j > 1`; for `s_j = 1` by A3). Separation of `theta` from `theta*` therefore means a lower bound on `Psi_m` over **all** belief pairs a policy can start a block at, not an ergodic average.

### 4.2 Proposition 4.2 (explicit burst separation). PROVED

Let `m_1 >= 1` be such that `kappa_stat := min_{theta in Theta_conf} KL(S^{theta*}_{m_1} || S^theta_{m_1}) > 0`. It exists: each `theta in Theta_conf` is non-equivalent, so some block length `m_theta` has distinct stationary block laws, KL is nondecreasing in block length (data processing), and `Theta_conf` is finite. Put `M_1 := m_1 L` and

`r_0 := ceil( log( max{ 4 [M_1 + 2 (e^{M_1} - 1)] / kappa_stat , 2 (e^{M_1} - 1) } ) / log(1/varrho) )`.

Then for every `m >= m_1 + r_0` and **every** pair of beliefs `(b*, b)` on `Z` (not only reachable ones), `Psi_m(b*, b) >= kappa_stat / 2`. So A6 holds with `kappa_0 >= kappa_stat/2`.

*Proof.* (1) By data processing `Psi_m(b*, b) >= Psi_{m_1+r_0}(b*, b) >= KL(P || Q)` where `P`, `Q` are the laws of the **last `m_1` outputs** of the first `m_1 + r_0`: `P = sum_z (b* A_{theta*}^{r_0})(z) P^{theta*}_{z, m_1}`, `Q` likewise for `theta`.
(2) Dobrushin: `A = K a_- U + (1 - K a_-) A~` (`U` uniform), so `TV(beta A^k, pi) <= varrho^k`. Hence `P` and `P' := S^{theta*}_{m_1}` are mixtures of the same block pmfs `P_z` with weights within TV `tau := varrho^{r_0}`; same for `Q, Q'`.
(3) Each `P_z(y) in [g_-^{m_1}, g_+^{m_1}]`, so `max_z P_z(y)/min_z P_z(y) <= e^{M_1}` and `|P(y) - P'(y)| <= tau (max_z P_z(y) - min_z P_z(y))`, giving `|P/P' - 1| <= tau (e^{M_1} - 1) <= 1/2` (second term in `r_0`) and `|log P/P'| <= 2 tau (e^{M_1} - 1)`.
(4) With `ell = log P/Q`, `|ell| <= M_1`: `|KL(P||Q) - KL(P'||Q')| <= sum|P - P'| M_1 + sum P' (|log P/P'| + |log Q/Q'|) <= 2 tau [M_1 + 2 (e^{M_1} - 1)] <= kappa_stat/2` (first term in `r_0`). So `KL(P||Q) >= kappa_stat/2`. QED.

*Remarks.* (i) Compactness gives a non-constructive alternative (`Psi_m` nondecreasing in `m`, continuous on a compact set, and `{Psi_m = 0}` decreasing with empty limit because equal laws from all start beliefs force equal stationary laws); I use the explicit route. (ii) The explicit route is very conservative: it wastes `r_0` labels per block (see Section 7: Toy A has `r_0 = 43`).
(iii) **By-product (PROVED):** for a single consecutive run of `n` labels from stationary starts, `E[S_n] = D_n >= floor(n/m) kappa_0`, so `liminf D_n/n >= kappa_0/m > 0`: positivity of the KL rate without citing DMOvH Thm 12.

### 4.3 When L2 fails (counterexamples)

**(a) Single-query separation is false in general. PROVED (algebra) + numerics.** Toy B: `theta*`: `A = [[.9,.1],[.3,.7]]`, `P(+1|z) = (.7, .1)`; `theta_0`: IID Bernoulli(.5). `R_theta* = [.3, .9]` in the first coordinate. At predictive belief `b = 2/3 in R` the predictive `P(+1) = .7 b + .1 (1 - b) = .5` exactly, so `Psi_1(b) = 0` (script: `-5.6e-17`), and the minimum over `R` of `Psi_1` is 0. A predictable policy tailored to `(theta*, theta_0)` that queries only near this belief gets `O(eta^2)` information per query; hence **no `kappa_sep` is uniform over all predictable policies**. The minimum of `Psi_m` over `R` becomes positive at `m = 2` (0.0192), `m = 3` (0.0424), `m = 8` (0.161).
Non-identifiable-but-not-decision-relevant pairs must be quotiented (`Theta_conf`); non-identifiable decision-relevant pairs (`theta ~ theta*` but with `mu_t` sign conflict) cannot be excluded at all, which is why the burn-in `t_f` and margin `gamma_0` are needed.

**(b) Calendar of single queries with spacing `g` fails when separation is by dynamics only. PROVED bound + exact numbers.** Toy A: `theta*`: symmetric `a = .3`, `theta`: symmetric `a = .1`, same emissions `P(+1|z) = (.8, .2)`; both stationary laws are uniform, so all single-label stationary marginals coincide and `m_1 = 2` (stationary pair KL: 0.0110 and 0.0108). With spacing `g` the belief at each query is within `varrho^g` of `pi` for both models, so the per-query conditional KL is `<= (0.6 (0.4^g + 0.8^g))^2 / 0.16`, decaying like `0.64^g`. Exact `D_10/10` (stationary start): `g=1: 1.7e-2`, `4: 8.8e-3`, `8: 1.6e-3`, `12: 2.8e-4`, `16: 4.6e-5`. Per-query information decays geometrically in the spacing relative to the persistence time. (If the single-label stationary marginals differ, the same argument as Prop. 4.2 with `m_1 = 1` shows spacing is harmless up to `O(varrho^g)`; the failure is specific to dynamics-only separation. This is the sharp form of vacuity item 4 in the sketch.)

**(c) Unreleased-data-dependent queries break everything**: Section 2.

## 5. L3: LLR concentration at the 1/kappa rate. PROVED (burst class)

**Truncation.** Under A3 every block log-ratio is bounded deterministically: `|Lambda| <= M := mL`, because each block pmf `P_z(y_{1:m}) in [g_-^m, g_+^m]`. So no truncation is needed. (For unbounded log-ratios a truncation at level `L_tau` would add `P(|l| > L_tau)` terms and replace `M`; I did not carry this out: CONJECTURE for non-floored continuous emissions.)

**Lemma 5.1 (variance-KL). PROVED.** For pmfs `p, q` with `|log p/q| <= M`: `E_p[(log p/q)^2] <= (2 + M) KL(p||q)`.
*Proof.* `KL(p||q) = E_q[phi(r)]`, `phi(r) = r log r - r + 1 >= 0`, `r = p/q`, and `E_p[(log r)^2] = E_q[r (log r)^2]`. With `u = log r`, `phi~(u) := u e^u - e^u + 1 >= 0`. For `u >= 0` let `F(u) = (2 + u) phi~(u) - u^2 e^u`; `F(0) = 0`, `F' = phi~ >= 0`, so `F >= 0`. For `u <= 0` let `G(u) = 2 phi~(u) - u^2 e^u`; `G(0) = 0`, `G' = -u^2 e^u <= 0`, so `G >= 0` on `u <= 0`. Hence `r (log r)^2 <= (2 + max(u,0)) phi(r) <= (2 + M) phi(r)`. Take `E_q`. QED. (Numerics: max violation of the pointwise inequality on a fine grid is `-3.3e-4`; the realized ratio `E[Lambda^2]/((2+M) Psi)` over belief grids is at most 0.37, so the constant is conservative by at least 2.7x.)

**Lemma 5.2 (one block). PROVED.** Let `Lambda_k` be the block LLR of burst `k`, `Psi_k = Psi_m(b*_k, b_k) >= kappa_0` its conditional mean given the start, and `lambda := 1/(2(2 + M))`. Then
`E_{theta*}[ e^{-lambda Lambda_k} | F_start ] <= 1 - lambda Psi_k / 2 <= exp(-lambda kappa_0 / 2)`.
*Proof.* `|lambda Lambda| <= lambda M < 1/2` and `e^{y} <= 1 + y + y^2` for `y <= 1`, so `E e^{-lambda Lambda} <= 1 - lambda Psi + lambda^2 E Lambda^2 <= 1 - lambda Psi + lambda^2 (2 + M) Psi = 1 - lambda Psi (1 - lambda (2 + M)) = 1 - lambda Psi/2`, using Lemma 5.1 at block level. QED. (Exact check on belief grids: `max[mgf - (1 - lambda Psi/2)] < 0` in all cases tested, e.g. `-1.9e-3` for Toy A `m=6`.)

**Proposition 5.3 (uniform-in-time exclusion). PROVED (modulo Ville's inequality).** Let the policy be in `Q_m(B)`, `theta in Theta_conf`, `c := log(1/(alpha pi*))`, `c_m := c + (m - 1) L`, and
`N_theta := ceil( [ 2 c_m + 4 (2 + mL) log(1/delta') ] / kappa_0 )`.
Then with `P_{theta*}`-probability at least `1 - delta'`, **simultaneously for all times** at which the policy has at least `N_theta` complete bursts released, the gate's confidence set excludes `theta`.
*Proof.* Let `S^{(N)} = sum_{k<=N} Lambda_k` (block boundaries). `Z_N := exp(-lambda S^{(N)} + lambda kappa_0 N/2)` is a nonnegative supermartingale (Lemma 5.2) with `Z_0 = 1`, stopped at the number of executed bursts. Ville: `P(sup_N Z_N >= a) <= 1/a`. On `{S^{(N')} <= c_m for some N' >= N}`, `Z_{N'} >= exp(lambda (kappa_0 N/2 - c_m))`; the choice of `N_theta` makes this `>= 1/delta'`. So with probability `>= 1 - delta'`, `S^{(N')} > c_m` for all `N' >= N_theta`. At a time `t` with `N_c >= N_theta` complete released bursts and a partial burst of `< m` released labels, `S_{j(t)} >= S^{(N_c)} - (m-1) L > c`, hence `E_t(theta) >= pi* e^{S_{j(t)}} >= 1/alpha` and `theta notin C_t`. QED.

**Constant-factor slack (honest list).** (1) Factor 2 on `c_m` (half-drift in the Chernoff step); Wald in the IID case has factor 1. (2) The coefficient `4 (2 + mL)` on `log(1/delta')` (variance-KL constant times `1/lambda`); the numerics suggest at least ~2.7x of it is slack. (3) The offset `(m-1) L` from mid-burst times. (4) The `1/kappa_0` is for blocks; per label it is `m/kappa_0 = 1/kappa_sep`.
**Fallback rate.** Plain Azuma-Hoeffding on the centred block martingale (range `2M`) gives `N >= 2 M^2 log(1/delta') / kappa_0^2`-type conditions (rate `1/kappa^2`); I do not need it. (Azuma and Freedman are textbook inequalities not in the repo audits: needs source check for a formal citation; the 1/kappa result above is proved without either.)

## 6. Theorem C1-B and the wall-clock / tightness comparison

**Theorem C1-B (burst class). PROVED-MODULO Ville's inequality and Theorem C1-A (`switching_theory_targets_c1_c2_v1.md` 1.2).**
Assume A1-A6, a policy in `Q_m(B)` with `B >= m N*`, margin `gamma_0`, burn-in `t_f` (Cor. 1.3), and

`N* := ceil( [ 2 c_m + 4 (2 + mL) log(|Theta_conf| / delta) ] / kappa_0 )`, `n* := m N*` (released labels),

with `c_m = log(1/(alpha pi*)) + (m-1) L`, `kappa_0 = m kappa_sep`. Then with `P_{theta*}`-probability at least `1 - alpha - delta`, for every `t` such that (i) at least `N*` complete bursts have been released by `t`, (ii) `t >= t_f`, and (iii) `mu_t(theta*| O_t) > h + gamma_0`, the gate promotes at `t`. In particular the first promotion time satisfies `tau <= min{ t : t >= max(t_f, e_{N*} + d), mu_t(theta*) > h + gamma_0 }`, where `e_{N*}` is the event index of the last query of burst `N*`.

*Proof.* Event `E_cov`: `theta* in C_t` for all `t` (probability `>= 1 - alpha`, Theorem C1-A / Ville). Event `E_ex`: Prop. 5.3 for every `theta in Theta_conf` with `delta' = delta/|Theta_conf|` (probability `>= 1 - delta`, union bound). On both, at a time satisfying (i)-(iii): `C_t` is non-empty (contains `theta*`) and its elements are (a) `theta' in [theta*]`: `mu_t(theta') >= mu_t(theta*) - 4 rho_F^{t-1} > h` by Cor. 1.3 and (ii); or (b) `theta notin Theta_conf union [theta*]`: by definition of `Theta_conf` (conflict needs `mu_t(theta*) >= h + gamma_0`, which holds by (iii) and `t >= t_f`) we get `mu_t(theta) > h`. Elements of `Theta_conf` are excluded by `E_ex`. So `min_{C_t} mu_t > h`. QED.

**Wall-clock.** Front-loaded run (`q = 1`: blocks back-to-back from event 1): `e_{N*} = n*`, so `tau <= max(t_f, n* + d)` up to the first beneficial `t` after that, and `B >= n*` is required. With a duty cycle `q in (0, 1]` (fraction of events queried, gaps between bursts of arbitrary length) the same bound holds with `e_{N*} = n*/q`: wall-clock `d + n*/q`. Under a cap `B` over horizon `T` the sustainable average duty cycle is `B/T`, so `q <= B/T` if the budget must last the horizon; promotion by wall-clock `W` needs `n*` released within `W - d` events, i.e. `q >= n*/(W - d)` and `B >= n*`. **Gaps do not matter for information**: `Psi_m >= kappa_0` uniformly over start beliefs, which is exactly why a calendar of *bursts* works where a calendar of *single queries* does not (4.3b). Delay `d` is purely additive (Lemma 0(i)) and, by Cor. 1.2(d), also caps what the beneficial event can look like: it is a `d`-step-ahead prediction.

**Comparison with C1-C.** The sketch's floor (valid when `Theta` contains an everywhere-bad single-state model `theta_0` and `theta*` is an HMM) is `t >= d + kl(1-gamma||alpha)/kmax`, `kmax = max_z KL(g_{theta*}(.|z) || g_{theta_0})`, `kl(1-gamma||alpha) >= (1-gamma) log(1/alpha) - log 2`. (C1-C was taken from the theory-targets doc; I did not re-verify its proof here.) Writing the upper bound per label,
`n* <= m + [2 c_m + 4 (2+mL) log(|Theta_conf|/delta)] / kappa_sep`,
the ratio of upper to lower bound is, to leading order,

`(kmax / kappa_sep) * [ 2 c_m + 4 (2+mL) log(|Theta_conf|/delta) ] / kl(1-gamma||alpha)`.

Gap factors: (1) KL condition number `kmax/kappa_sep` (measured 7.5-10 on Toy C, including the `m`-block overhead), (2) the constant 2 and the `(2+mL) log(1/delta)` term versus `log(1/alpha)`, (3) `log(1/pi*)`, `log|Theta|`, and the `(m-1)L` offset. Tight to a constant only in the IID two-point case (`m = 1`: `[2 c + 4 (2+L) log(1/delta)]/kappa` versus Wald's `c/kappa`). The **order** is `d + Theta(log(1/alpha)/kappa)` for fixed family constants, with `kappa` the burst-separation constant; it is not tight in the constants, and the explicit-forgetting version of `kappa_0` is off by orders of magnitude (Section 7).

## 7. Numerical checks of the key constants (scratch; empirical slack reported as observed)

All on finite-alphabet two-state HMMs, `alpha = delta = .05`, `pi* = .5` (`c = log 40 = 3.689`), natural logs. Monte Carlo: 1000 paths, one seed, stationary starts, consecutive queries; "uniform-exclusion time" = last label index at which `S_j < c` on a path, then the 95th percentile (and the median) over paths.

**Toy B (HMM vs IID).** `theta*`: `A = [[.9,.1],[.3,.7]]`, `P(+1|z) = (.7,.1)`, stationary `(.75,.25)`, `g_- = .1`, `g_+ = .9`, `L = 2.197`. Block separation `min_{b in R} Psi_m`: `m=1: 0` (at `b = .667`), `2: .0192`, `3: .0424`, `5: .0899`, `8: .1606`, `12: .2545`. Stationary block KL: `m=1: .0050`, `2: .0234`, `12: .2566`.

**Toy C family (scaling in `kappa`).** `theta*_eps`: symmetric `a = .1`, `P(+1|z) = (.5+eps, .5)`; vs IID `.5`; `m` chosen per row to minimise `n*` over `{1,2,3,4,6,8,12,14}`; `kappa_0 = min_{b in R} Psi_m` (grid, 401 points).

| eps | KL rate (MC) | `kmax` | C1-C floor `kl(.95||.05)/kmax` | MC exclusion time median / q95 | proven `n*` (m, `kappa_0`, `N*`) | `n*`/q95 | `kmax/kappa_sep` | `n* * rate` |
|---|---|---|---|---|---|---|---|---|
| .40 | .1037 | .3681 | 7.2 | 48 / 181 | 6824 (8, .3201, 853) | 37.7 | 9.2 | 708 |
| .30 | .0518 | .1927 | 13.7 | 95 / 309 | 9144 (8, .1607, 1143) | 29.6 | 9.6 | 474 |
| .20 | .0213 | .0823 | 32.2 | 230 / 731 | 15136 (8, .0658, 1892) | 20.7 | 10.0 | 323 |
| .10 | .0051 | .0201 | 131.6 | 930 / 2733 | 36732 (12, .0322, 3061) | 13.4 | 7.5 | 186 |

Reading: the empirical exclusion time scales like `1/rate` (`q95 * rate` = 18.8, 16.0, 15.6, 13.9), consistent with 1/kappa and **inconsistent** with 1/kappa^2. The proven `n* * rate` is non-increasing as `rate` falls, again not 1/kappa^2 behaviour (the `(2+mL)` factor shrinks as `eps` shrinks, which partly offsets). The proven bound is 13-38x above the MC q95 and 280-950x above the C1-C floor.

**Toy A (dynamics-only separation).** `theta*` `a = .3` vs `theta` `a = .1` (and reverse), `P(+1|z) = (.8,.2)`, `L = log 4 = 1.386`, uniform stationary laws. `min Psi_m` for `*=.3`: `m=2: .0110`, `4: .0473`, `6: .0881`, `12: .2113`. Best proven `n*` with the exact min-over-belief `kappa_0`: **8984** (`m = 4`, `kappa_0 = .0473`, `N* = 2246`) for `*=.3`, **8476** for `*=.1`. Monte Carlo (rate .0205/label): exclusion time median 219, q95 621 labels. With the **explicit forgetting-based** `kappa_0 = kappa_stat/2` of Prop. 4.2: `r_0 = 43`, `m = 45`, `kappa_0 = .00551`, giving `n* = 7.36e6` for `*=.3` (7.52e6 for `*=.1`): about 800x worse than the min-over-belief version and 10^4 times the MC q95. So Prop. 4.2 establishes positivity and the structure of `kappa_0`, but its constants are not usable. (`kmax = .832` for this family, so `kmax/kappa_sep` is about 70 with the min-over-belief `kappa_sep = .0473/4` and about 7000 with the explicit one; the C1-C floor does not apply because Toy A has no everywhere-bad single-state member.)

**Other checks.** Lemma 5.2 mgf inequality and the variance-KL ratio: verified on grids (Section 5). Lemma 0: exact enumeration (Section 2). L1: exhaustive (Section 3).

## 8. What remains for a full C1 theory section

1. **Non-burst predictable policies.** L2/L3 are false for general predictable policies (4.3a). A theorem for adaptive acquisition (the part of C1 that could be a contribution) needs a policy class with a belief-region guarantee: the block bound with `kappa_0` replaced by `min` over the belief region in which the policy commits to start blocks. This is the natural container for C1-E (persistence-aware querying) and is **not proved**; note the policy only sees its own filter, not `b*`, so relating the region to `b*` needs an extra filter-error argument (L1 supplies the tool). CONJECTURE.
2. **Sharper constants.** (a) Replace Prop. 4.2's continuity step (800x slack on Toy A) by a direct bound on `min Psi_m` using the Hilbert-metric rate `(1-r)/(1+r)` (needs source check) or a computable certificate over the belief simplex; (b) tighten `4(2+mL)` (Bhattacharyya/Hellinger Chernoff at `lambda = 1/2` is the obvious route; not done); (c) remove the factor 2 (sequential-test argument instead of Chernoff).
3. **Single long run.** `E[S_n] >= n kappa_rate - C` with `kappa_rate := E[KL(P(.|infinite past) || Q(.|infinite past))]` follows from L1 (finite-past vs infinite-past predictives differ by `O(rho_F^i)`) plus a KL-continuity estimate, with `kappa_rate >= kappa_0/m` from 4.2(iii). Route clear; constants not written. CONJECTURE (not needed for Theorem C1-B).
4. **Latent-regime onset to beneficial event.** The probability that `mu_t(theta*) > h + gamma_0` within a stated number of events of a latent regime onset (given released labels, delay `d`, persistence) is a change-detection-with-delay statement and is **not covered**. Cor. 1.2(d) gives only the vacuity side. This is where the "after the regime becomes beneficial" wording of the task would have content, and it interacts with the window analysis of C2.
5. **Lower bound for HMM pairs.** C1-C as stated needs an everywhere-bad single-state `theta_0`. A general-pair floor of the form `kl(1-gamma||alpha)/kappa_max(theta*, theta)` with `kappa_max = max_{b*, b} KL` of one-step predictives needs the "every promotion is false under `theta_0`" hypothesis replaced by something checkable; I did not do this.
6. **Misspecification and drift** remain out of scope (Prop. C1-D1(iii) of the theory doc).
7. **Source checks before any write-up.** Formal citations for Ville, Azuma/Freedman, Birkhoff-Hopf contraction; a read of DMR Thm 6 text to confirm the printed constant; Arnold et al. and Emmenegger et al. remain the cited methods for the coverage step (audit verdict: PARTIAL, corollary by proof pattern).
8. **R2 position.** After this appendix no *proof tool* in C1-B is new: coverage is Ville plus the transcript factorization (Lemma 0); forgetting is a Doeblin argument; concentration is a Chernoff bound with a variance-KL inequality. What is HMM-and-contract-specific is (i) the burst-uniform separation and its failure modes (4.3), (ii) the delay-as-additive-clock accounting, (iii) the quotienting by decision-equivalence with a forgetting margin. That is thin for a headline contribution and adequate for a supporting theorem.

## 9. Continue / pivot / stop

- **C1-B as a supporting theorem: CONTINUE (narrowly).** The sketch's broken steps are now repaired for a clean policy class, the 1/kappa rate is proved, and the failure modes are explicit and numerically illustrated. Do not claim the explicit-forgetting constants or the tightness; the measured gap to the C1-C floor is 280-950x with a 7-10x condition number. Keep as a baseline/analysis section with Theorem C1-A.
- **C1 as a headline: do not expand on this evidence.** It stays dependent on C1-E (belief-region-restricted blocks, item 1 above); that is the only remaining route to a rate-level separation, and the Kapoor-Nair R6 comparison still applies.
- **STOP signals recorded:** none triggered. A stop would be a source theorem giving exclusion rates under delayed predictable sampling for HMM families; none of the audited sources does, but the audit covers only those sources.
