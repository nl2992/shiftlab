# Theory targets for C1 and C2 (and a C3 note) under R1-R6

**Date:** 2026-10-30. **Status:** THEORY-TARGET analysis. No result in this file is a validated novelty claim. Proof status is
labelled per statement: **PROVED** (full proof given here), **PROOF SKETCH** (route and the precise unproved step named),
**CONJECTURE** (no proof). Nothing here was run on repository data. Two scratch numerical checks were run outside the repo
(Section 5). Per the 2026-10-30 revision, a target is only a *setting contribution* if (i) it is not a source theorem or direct
corollary under the same contract (R2), (ii) its proof needs a stated nontrivial step, and (iii) a lower bound or separation shows
the contract matters.

Source-status convention. "Audited" means the repository audit docs record a primary-source theorem-level read (I relied on those
records, I did not re-read the papers). "Log-only" means the source is cited in a candidate doc but I found no theorem-level read
recorded in what I read (Arnold et al., Kapoor-Nair, Emmenegger-Mutny-Krause, Huang-Bickford Smith-Rainforth). "Needs source check"
means it is not in the repo audits at all (filter-stability and HMM identifiability literature, Kontorovich-Ramanan-type
concentration); I name these only as the places a proof would have to look, not as citations.

---

## 1. C1: delayed-HMM predictive confidence-set gate

### 1.1 Contract (restating the registered candidate, with the extra assumptions the proofs below need)

- Finite family `Theta`, prior `pi` with full support. For each `theta`: a K-state HMM with transition `A_theta`, emission law
  `g_theta(. | z)` on a finite alphabet (or a common dominating measure) in `[-1,1]`, initial law `nu_theta`. No covariates
  (or a parameter-free covariate law with emissions conditional on covariates; I omit this).
- One query per event at most, at most `B` on every path (pending included). Query for event `s` is decided at time `s` by a
  kernel `kappa` that is a function of the observable history (released labels, past queries/actions) and fresh randomness, the same
  for every `theta`. Label of event `s` is released at the start of `s+d`, `d>=1`, in event order. Querying does not affect the
  outcome process.
- `O_t` = observable history before the action at `t`. `mu_t(theta) = E_theta[X_t | O_t]`, computed by the delayed HMM forward filter.
- Gate: `C_t = {theta : E_t(theta) < 1/alpha}`, `E_t(theta) = sum_{theta'} pi(theta') L_t(theta')/L_t(theta)`; promote at `t` iff
  `C_t` nonempty and `min_{theta in C_t} mu_t(theta) > h`.
- **False promotion (model-conditional):** promotion at some `t` with `mu_t(theta*) <= h`, where `theta*` is the true parameter.

### 1.2 Target (a): anytime false-promotion control. PROVED (supporting, not novel)

**Theorem C1-A.** Under the contract above, for every `theta* in Theta` and every predictable query policy,
`P_{theta*}(exists t : promoted at t and mu_t(theta*) <= h) <= alpha`, simultaneously over all promotions and rollbacks (no episode
alpha-spending is needed).

*Proof.*

Step 1 (released-label factorization). Let `Y_1, Y_2, ...` be the released labels in release order, with event indices
`s_1 < s_2 < ...`. Because release is order-preserving and the query at event `s` is a function of labels released by time `s`
(all of which have smaller index than `s`, hence smaller position in the sequence), each `s_j` is a deterministic function
`sigma_j(Y_1,...,Y_{j-1}, U)` of earlier released labels and the policy's private randomization `U` (independent of the outcome process and
of `theta`). Condition on `U`. For a fixed value path `y_{1:j}`, the event `{Y_1=y_1,...,Y_j=y_j}` equals
`{X_{s_1}=y_1,...,X_{s_j}=y_j}` for the *fixed* integers `s_i = sigma_i(y_{<i})`. Hence under `P_theta`

`P_theta(Y_j = y | Y_{<j} = y_{<j}) = p_theta(y | y_{<j}) := P_theta(X_{s_j}=y | X_{s_i}=y_i, i<j)`,

the HMM conditional law of one event given earlier queried values (all unqueried and pending events marginalized). The pending labels
of events in `(s_j - d, s_j)` are not conditioned on, matching the registered "do not pretend pending outcomes are observed" rule.
(The repo's `check_switching_delayed_hmm_likelihood.py` verifies this factorization by exhaustive enumeration in one cell.)

Step 2 (supermartingale). For `theta' in Theta` set `M_j(theta';theta) = prod_{i<=j} p_{theta'}(Y_i|Y_{<i}) / p_theta(Y_i|Y_{<i})`
(denominators vanish only on transcripts of `P_theta`-probability zero, so the ratio is a.s. finite). Then
`E_theta[M_j / M_{j-1} | Y_{<j}] = sum_{y : p_theta(y|.)>0} p_{theta'}(y|.) <= 1`, so `M(theta';theta)` is a nonnegative
supermartingale under `P_theta` in the filtration `sigma(Y_{<=j})` with `M_0=1`. The mixture
`E_j(theta) = sum_{theta'} pi(theta') M_j(theta';theta)` is a nonnegative supermartingale with `E_0=1`.

Step 3 (Ville). The gate's `E_t(theta)` equals `E_{j(t)}(theta)` with `j(t)` the number of labels released by `t`; the supremum over
`t` is the supremum over `j<=min(B,T)`. Ville gives `P_{theta*}(sup_j E_j(theta*) >= 1/alpha) <= alpha`; the event is exactly
`{exists t : theta* not in C_t}`.

Step 4 (containment). On `{theta* in C_t}` a promotion requires `min_{C_t} mu_t > h`, so `mu_t(theta*) >= min_{C_t} mu_t > h`. Hence
`{false promotion} subset {exists t : theta* not in C_t}`. QED.

Remarks. (i) Any functional `f(theta, O_t)` of the `theta`-conditional law works in place of `mu_t`, e.g. the window mean
`sum_{u=t}^{t+W} E_theta[X_u | O_t]` (safety for a *model-conditional* future window; still not a statement about realized latent signs).
(ii) The proof uses the empty-confidence-set convention "do not promote". (iii) Ville is applied to the *whole* parameter confidence
set, so the price of arbitrarily many promotions is zero extra alpha; this is a different null from the repo's causal conditional null
(episode alpha spending controls the broader null and has power only against it).
(iv) R2 status: this is a direct corollary of anytime-valid likelihood-ratio confidence sets (Emmenegger-Mutny-Krause, log-only) and,
plausibly, of Arnold et al.'s sequential model confidence sets applied to forecasters `{f_theta}` (log-only; the check is whether their
theorem allows predictable sampling and delayed release). Treat (a) as supporting, as the registered doc already does.

### 1.3 Target (d): separation from distribution-free gates. PROVED (elementary), with a caveat that it is assumption-supplied

**Proposition C1-D1.** (i) [in-repo impossibility, `switching_information_risk_contract_v1.md`, goals log 2026-10-29] Any gate with
uniform distribution-free false-promotion risk `<=alpha` has first-opportunity promotion probability `<=alpha` in every environment,
because two environments with identical pre-action observations and benefits `X_1=-1` vs `+1` are indistinguishable before the first
action when `d>=1`. (ii) Let `Theta_good = {theta : mu_1(theta) > h + gamma0}` (all family members forecast benefit before any label).
If `Theta = Theta_good`, the C1 gate promotes at `t=1` with probability 1 (`C_1 = Theta`, `min mu_1 > h`) and satisfies Theorem C1-A. (iii) On
the out-of-model environment of (i) with `X_1=-1`, the same gate false-promotes with probability 1.

This is the whole separation at the first opportunity: the model class *is* the pre-action information that (i) says is necessary.
It is a statement that the contract matters (R2 requirement), not evidence of power. A less trivial separation (stale evidence after a
reversal) is **CONJECTURE C1-D2**: in a sticky symmetric two-state HMM with emission margin and delay `d` smaller than the persistence
time, a historical-benefit e-process gate (promote when cumulative released benefit wealth exceeds `1/alpha`) has
`P(promotion with mu_t(theta*) <= h) >= c > alpha` for a constant `c` not shrinking with `T`, whereas C1 stays at `alpha`. Route: after
a reversal the released labels at `s+d` lower `mu_t` while the historical wealth decays only linearly; an explicit small-cell
enumeration (like the existing exact checks) would confirm it. Not run.

### 1.4 Target (c): lower bound on promotion delay and budget. PROVED (reuses the in-repo KL argument)

**Proposition C1-C.** Suppose `Theta` contains `theta_0` with a single state (IID) and `mu_t(theta_0) <= h` for every history, and
`theta_1` an HMM. Let `kmax = max_z KL(g_{theta_1}(.|z) || g_{theta_0})`. Let a gate satisfy the model-conditional false-promotion
bound `<=alpha` under `theta_0` (every promotion is then false). Then for every `t`, with `n_t = min(B, (t-d)_+)`,

`P_{theta_1}(promote by t) <= beta_alpha(n_t * kmax)`,

where `beta_alpha` is the upper binary-KL inverse of `switching_noisy_information_lower_bound_v1.md`. Consequently, power `>= 1-gamma`
by time `t` requires `kl(1-gamma || alpha) <= kmax * min(B, t-d)`, i.e.

`B >= kl(1-gamma||alpha)/kmax`, `t >= d + kl(1-gamma||alpha)/kmax`, and `kl(1-gamma||alpha) >= (1-gamma) log(1/alpha) - log 2`.

*Proof.* Identical to the in-repo proof. The transcript `O_t` contains at most `n_t` labels with `theta`-dependent law (labels of events
`<= t-d`, at most `B` queried). Chain rule for the learner transcript with common kernels gives
`KL(P_1(O_t)||P_0(O_t)) <= sum over released labels of E_1[KL(p_{theta_1}(.|y_{<}) || g_{theta_0})]`. Each conditional predictive under
`theta_1` is a filter-weighted mixture `sum_z b(z) g_{theta_1}(.|z)`; convexity of `KL(. || Q)` in its first argument bounds each term
by `kmax`. Data processing on `{promote by t}` and the false-promotion constraint `P_0(promote by t) <= alpha` finish as in the repo. QED.

The bound is the existing result with the per-label constant replaced by a state-resolved `kmax`. It is not claimed to be new.
**Observation (genuinely HMM-specific, and where the contract matters).** `kmax` is a *per-state* constant; the output-process KL
*rate* `kappa_rate = lim (1/n) KL(P_{theta_1}^{(n)} || P_{theta_0}^{(n)})` is roughly the stationary occupancy of the informative state
times `kmax` when the informative state is rarely visited. A schedule that queries every event wastes budget on uninformative regimes;
the lower bound permits budget as small as `kl/kmax`. This is the room an adaptive, persistence-aware query rule could exploit
(Conjecture C1-E below).

### 1.5 Target (b): promotion-delay / sample-complexity upper bound. PROOF SKETCH (conditional on three unproved lemmas)

**Assumptions.**
- (U1) Uniform ergodicity: every `A_theta` satisfies a Doeblin/strong-mixing condition with forgetting rate `rho < 1` for the HMM filter
  (e.g. `rho = ` Birkhoff contraction coefficient of the positive matrices). *Needs source check* (HMM filter stability, e.g. Le Gland-Mevel,
  Douc-Moulines-Olsson-van Handel type results; none are in the repo audits).
- (U2) Emission floor: `g_theta(y|z) >= eps0 > 0`, so predictive log-ratios are bounded: `|log p_{theta*}(y|y_<)/p_theta(y|y_<)| <= L := log(1/eps0)`.
- (U3) Identifiability margin: `kappa_sep(theta*) := min over non-equivalent theta of kappa_rate(theta*||theta) > 0`, where "equivalent" means
  identical stationary output-process law (then `p_theta = p_{theta*}` for all histories, so `mu_t(theta) = mu_t(theta*)`). Rate is for the
  schedule actually used; for "query every event" it is the Leroux KL rate of the full output process. *Needs source check* (Leroux-type
  characterization: rate zero iff equal output laws, under ergodicity and positivity).
- (U4) Query policy: query the first `n` consecutive events, then stop (this is a specific upper-bound policy, not claimed optimal).
- (U5) Evaluation at a time `t` with `mu_t(theta*) > h`.

**Claim (b).** Let `c = log(1/(alpha pi*))` with `pi* = pi(theta*)`. For `delta in (0,1)` there are constants `C_f, C_c` depending only on
`(L, rho, K)` such that if

`B >= n*(delta) := ceil( (c + C_f) / kappa_sep + C_c * log(|Theta|/delta) / kappa_sep^2 )`

then with probability at least `1-delta` under `theta*`, `C_t` contains only parameters equivalent to `theta*` at every `t >= n* + d`, hence
the gate promotes at the first `t >= n* + d + 1` with `mu_t(theta*) > h`. Together with Proposition C1-C, the promotion time is
`d + Theta( log(1/alpha)/kappa )` up to the factors listed in 1.6.

**Proof route.**
1. *(Deterministic)* `theta in C_t` implies `E_t(theta) < 1/alpha`; since `E_t(theta) >= pi* L_t(theta*)/L_t(theta)`, exclusion of `theta` follows
   from `LLR_n(theta*,theta) := log L(theta*)/L(theta) >= c`. After all non-equivalent `theta` are excluded, every survivor has
   `mu_t = mu_t(theta*)`, so the gate promotes iff `mu_t(theta*) > h`. (This step is rigorous.)
2. *(Drift; the nontrivial step)* `LLR_n = sum_i l_i` with `E[l_i | F_{i-1}] = KL(p_{theta*}(.|y_<) || p_theta(.|y_<)) >= 0`, so
   `E[LLR_n] = KL(P_{theta*}^{(n)} || P_theta^{(n)})` exactly. The claim `E[LLR_n] >= n kappa_rate - C_f` requires that the *conditional* KL
   at step `i` converges to `kappa_rate` geometrically, which holds because both filters, started from different initial laws, forget the
   initial condition at rate `rho` under (U1)-(U2) (each filter's predictive is a Lipschitz function of the past with
   total weight `sum_k rho^k`). **This is the filter-forgetting step under sparse delayed observation:** under a spacing-`g` schedule the
   observed subsequence is an HMM with transition `A^g` and forgetting `rho^g`, and the `d`-step delay appears only through the
   evaluation time of `mu_t`, not through the LLR. Unproved here; `C_f` is of order `L/(1-rho)`.
3. *(Concentration)* `LLR_n` is a `C_L`-Lipschitz function (coordinatewise constant `O(L/(1-rho))`) of the output sequence of a geometrically
   ergodic chain with emissions; a McDiarmid-type inequality for such sequences (Kontorovich-Ramanan type; *needs source check*) gives
   deviations `O((L/(1-rho)) sqrt(n log(1/delta')))`. This yields the `1/kappa_sep^2` term; union bound over `|Theta|-1` parameters gives
   the `log(|Theta|/delta)`. A Bernstein/Freedman route would need a concentration statement for the *sum of conditional KLs* (a function of
   the history, not a martingale) and is **CONJECTURE C1-B+**: it would replace `1/kappa_sep^2` by `1/kappa_sep`.
   (The elementary variance bound `E_p[(log r)^2] <= c_L KL(p||q)` for `r=p/q in [e^-L,e^L]` is available and would feed the Freedman step.)

**IID sanity case (K=1, fully provable).** For `Theta={theta_0,theta_1}` Bernoulli, Step 2 is exact (random walk with drift `kappa`) and the
bound reduces to the classical Wald/SPRT sample size plus delay `d`; the `1/kappa^2` term is a Hoeffding artifact (Hoeffding
suffices when `B >= max(2c/kappa, 8L^2 log(1/gamma)/kappa^2)`). Numerical check (Section 5.1): lower bound 94.7 labels, exact
Neyman-Pearson fixed-`n` 158, anytime LR e-process about 220 for `alpha=.05`, `gamma=.2`, `epsilon=.1`; constant-factor gaps (1.7x, 2.3x), as expected.
So in the IID case C1 (b)+(c) is classical (Wald; DAL's detector windows `O(log T + log(1/delta_F))` are the same order). **The HMM contribution
would be exactly steps 2-3 with a delay and a budget.**

### 1.6 Matching, vacuity and failure modes

Matching ratio between (b) and (c): `[ (c + C_f)/kappa_sep ] / [ ((1-gamma) log(1/alpha) - log 2)/kmax ]`
`~ (kmax/kappa_sep) * (1 + (log(1/pi*) + C_f)/log(1/alpha))`. So the pair is tight only up to (i) the **KL condition number**
`kmax/kappa_sep` (large when the informative state is rarely occupied or when hypotheses differ only in transition structure),
(ii) `log|Theta|` from a uniform prior, (iii) the filter-forgetting constant `C_f` (large for slow mixing), and (iv) the `1/kappa^2` slack.
It is tight to a constant in the two-point IID case.

Vacuous or failing regimes (each is a regime where the theorem is true but says nothing, or the gate is correctly silent):

1. `B < kl(1-gamma||alpha)/kmax`: no gate meeting the safety constraint can have power `1-gamma` (Prop. C1-C). The theorem region is
   `B >= n*`, which for small `kappa` or small `alpha` is large.
2. **Delay beyond persistence.** `mu_t(theta*)` is a `d`-step-ahead prediction from released labels. Writing `mubar` for the stationary
   mean, `|mu_t(theta*) - mubar| <= 2 rho^d` (Doeblin contraction of the `d`-step prediction). If `mubar <= h` and
   `2 rho^d < h - mubar + gamma0`, then `mu_t(theta*) <= h` on every history: promotion would be a false promotion, so *no safe gate may
   promote*. The model-conditional guarantee is then silent not because of inefficiency but because the model says the candidate is not
   currently beneficial in expectation. This is the "delay vs regime persistence" boundary and it is not removable by better acquisition.
3. Non-identifiable but decision-relevant parameters (`kappa_sep = 0` for some `theta` with `mu_t(theta) <= h < mu_t(theta*)`): the gate never excludes them;
   the refinement is to require exclusion only of `{theta : mu_t(theta) <= h}` (a *decision-relevant* separation `kappa_dec >= kappa_sep`).
   The sign-only formulation can be much cheaper but its bad set is history dependent, so I could not state a clean uniform-in-`t` version.
4. Weak mixing: `C_f ~ L/(1-rho)` and the `A^g`-subsampling ruin per-label information when `g` exceeds the regime duration; queries spaced
   farther than the persistence time observe a nearly IID mixture and the HMM filter has nothing to track.
5. Misspecification, parameter drift, out-of-family regime change: no guarantee (Prop. C1-D1(iii)).
6. Tiny `pi*`/large `|Theta|`: `c = log(1/(alpha pi*))` can dominate `log(1/alpha)`.

**CONJECTURE C1-E (persistence-aware querying; budget separation).** In a two-regime HMM family where only regime 2 is informative about the
`theta_1`/`theta_0` distinction (`kmax` achieved in regime 2, `~0` in regime 1) and regime duration is `>> d`, a policy that queries only when the
delayed filter assigns probability `>= 1-eta` to regime 2 reaches the promotion deadline with `B <= (1+o(1)) kl/((1-eta')kmax)` labels,
while every query schedule independent of released labels needs `B >= (1-o(1)) kl/(occ * kmax)`, `occ` = stationary occupancy of regime 2.
Wall-clock time is unchanged (`~ n*/occ` either way); the separation is in budget only. Proof route: coupling with the regime process, a
filter-error bound `O(rho^d)` for the regime-2 indicator, and the Prop. C1-C chain rule restricted to queried-in-regime-2 labels.
This is the one place the contract (delay + cap + persistence) enters a *rate*. It would be a separation from calendar/fixed schedules
only; against adaptive planners (Kapoor-Nair costed-sensing MDP, Huang-Bickford Smith-Rainforth decision-focused acquisition, both log-only)
it is at best an analysis of an instance of their policies, so by R2 it is a setting contribution only if the *bound itself* (with delay and
persistence dependence) is not in those papers.

### 1.7 R2 / R6 checklist for C1 (what to check, concretely)

For each source, the question is: does a stated theorem give (a), (b) or (c) under the same feedback, budget, delay and risk contract, or follow directly?
My prior expectation is "no" for all, but only the audits' summaries were read.

| Source (status) | Check to perform | Prior expectation |
|---|---|---|
| Gong-Zhang ICML 2026 (audited) | Do Thms 2.1-2.2, 3.1-3.2 (regret, budget phase transition) imply a time-to-promotion lower bound at false-promotion `alpha`? Embed the paired label as an observation subset; check whether the minimax instance gives a probabilistic (kl-type) constraint | No: regret vs fixed policy, immediate feedback, no safety event |
| Qiu et al. ICML 2026 (audited) | Delayed dynamic-regret wrapper (Alg. 4, Thm 5.2): does total-delay term yield any `d + log(1/alpha)/kappa` statement? | No: unconstrained OCO, no acquisition, no risk |
| Ryabchenko et al. COLT 2025 (audited) | Capacity `C` counts outstanding tracked rounds; confirm it cannot encode a total cap `B`; confirm fixed-delay minimax rate does not contain `kl(1-gamma||alpha)` | No |
| DAL (audited) | Property III.1 detector windows `m_D, ell_D = O(log T + log(1/delta_F) + log(1/delta_D))` are the IID analogue of (b). Check their detector's assumptions exclude HMM dependence; if a DAL-style detector holds under mixing, (b) in the IID-within-segment special case is covered | IID special case covered; HMM/delay/cap case not |
| Episode alpha spending, Tian-Ramdas online FWER (audited) | Different null (causal conditional vs model-conditional). Confirm C1-A is not implied: they control the broader null; compare *power* under the model on the same cell | Not implied; power comparison is the R6 item |
| Braverman et al. pacing (audited) | Hard budget regret vs pacing experts; confirm no safety/delay statement | No |
| Arnold et al. SMCS (log-only) | Read the theorem: do sequential model confidence sets with `{f_theta}` forecasters and predictable delayed sampling already give C1-A? Also whether they state any sample-complexity for exclusion | C1-A likely a corollary; (b)/(c) unknown, must read |
| Emmenegger-Mutny-Krause, Kapoor-Nair, Huang-Bickford Smith-Rainforth (log-only) | Theorem-level read: LR confidence sets (do they give a rate for exclusion?); costed-sensing suboptimality bound (does it translate to promotion budget?) | Unknown until read |
| Prabhu et al. TIT 2022 (audited), Li et al. usage-constrained / active two-sample (audited), Huang-Veeravalli finite-horizon QCD (audited) | Converse/achievability pairs for stationary IID with error constraints: confirm they give (b),(c) only for IID, no hard cap, no delay | IID covered; HMM+delay+cap not |
| Chick-Forster-Pertile 2017, Bayraktar-Ludkovski 2009 (audited) | Economic delayed sampling (stationary) and HMM switching (no cap, no delay, no risk) | Not the same problem |

---

## 2. C2: promotion versus reversal-monitor budget frontier

### 2.1 Model for the frontier

Promotion phase: IID null world `H0` (candidate not better) and alternative `H1`, per-label divergence `kP = KL(H1||H0)`; the policy has
`P_{H0}(promote) <= alpha`. Monitoring phase after a promotion at stopping time `tau`: no-reversal law `P0` vs reversal law `P1` with onset at
`tau` (worst case: immediate), per-label divergence `kR` (conditionally bounded by `kR` given any common past). The policy rolls back at time
`sigma`; spec: `P0(rollback by tau+m) <= beta` for all `m`, and `P1(rollback by tau+m) >= 1-gR` on the promotion event, averaged over promotion
histories. Labels: one query per event, delay `d`, pathwise cap `B` over the whole horizon (pending included).
Requirement for power in the promotion phase: `P_{H1}(promote by tP) >= 1-gP`.

Write `klP = kl(1-gP||alpha)`, `klR = kl(1-gR||beta)`.

### 2.2 Frontier lower bound. PROVED (standard ingredients; the sum-with-weight form is the content)

**Theorem C2-A.** Under 2.1, necessarily

`klP/kP + (1-gP) * klR/kR <= B`, and `n >= 2d - 1 + klP/kP + klR/kR` for the horizon (promotion deadline `tP >= d + klP/kP` followed by detection deadline `m >= d-1 + klR/kR`).

*Proof.*
(i) Promotion. Chain rule + data processing as in Prop. C1-C: `klP <= kP * E_{H1}[N^rel]`, `N^rel` = labels of events `<= tP-d` queried before `tP`
(only these have `H1`-dependent law). With `N^req >= N^rel` the number of requests before `tau` (pending included).
(ii) Monitoring on each promotion history. Labels of events before `tau` have the same law under `P0` and `P1` (reversal onset at `tau`), so they carry
zero information; the number of informative requests is at most `min(B - N^req(h), m-d+1)`. For a promotion history `h`, let `q(h)` and `p(h)` be the conditional
rollback-by-`tau+m` probabilities under `P1` and `P0`. Chain rule: `kl(q(h)||p(h)) <= kR (B - N^req(h))`. Joint convexity of `kl` and the spec give
`klR <= kl(E[q|prom] || E[p|prom]) <= E[kl(q||p) | prom] <= kR (B - E[N^req | prom])`, so `E[N^req | prom] <= B - klR/kR`.
(iii) Combine. `E_{H1}[N^rel] <= E_{H1}[N^req 1{prom}] + E_{H1}[N^req 1{not prom}] <= p_prom (B - klR/kR) + (1-p_prom) B = B - p_prom klR/kR` with
`p_prom >= 1-gP`. Hence `klP/kP <= B - (1-gP) klR/kR`. The horizon statement is the two single-phase deadline bounds added. QED.

Notes. (1) The weight `(1-gP)` is correct: non-promoted paths need no monitoring budget. (2) The statement is for *guarantee-type* specs (probability thresholds).
For utility-type objectives see 2.4. (3) The single-onset monitoring bound is what the registered candidate states; it does **not** scale with the horizon.
A multi-onset requirement should cost `~ (H/ell)` windows; see Conjecture C2-C. (4) Everything is a corollary of the in-repo noisy lower bound and the Huang-Veeravalli-type
window argument (audited); no novelty claimed.

### 2.3 Matching upper bound with split `rho`. PROOF SKETCH for the promotion half, CONJECTURE for the unknown-onset monitoring half

Policy: promotion by the LR e-process (anytime level `alpha`), query consecutively, hard sub-cap `BP = rho B`; after promotion, monitor with a delayed
mixture e-detector / CUSUM on labels queried on a calendar of spacing `Lc`, sub-cap `BR = (1-rho) B`.

*Promotion half (PROVED under bounded log-likelihood ratios `|log LR| <= L`).* Hoeffding: `P(LLR_{BP} < a) <= exp(-(BP kP - a)^2/(2 BP L^2))`,
`a = log(1/alpha)`. Therefore power `>= 1-gP` if `BP >= max(2a/kP, 8 L^2 log(1/gP)/kP^2)`. Compare lower bound `~ (1-gP) a/kP`: matching in the first term to a factor 2, with a
Hoeffding `1/kP^2` slack (the usual Bernstein refinement closes it for bounded-variance LLRs; not proved here).

*Monitoring half.* A mixture over onsets with weights `w_nu >= 1/H` and the e-detector threshold `1/beta` controls false rollback `<= beta` (Shin-Ramdas-Rinaldo, audited).
Detection requires `m_R ~ log(H/(beta gR'))/kR` informative labels after the reversal; with calendar spacing `Lc`, detection delay is `d + Lc m_R`. For a deadline `ell`,
`Lc <= (ell - d)/m_R`, so the *needed* cap is `BR ~ H_R m_R/(ell - d)` with `H_R` the remaining horizon, i.e. proportional to `H_R/ell`.
The single-onset lower bound `klR/kR` has no such factor, so (b)-upper and (a)-lower do not match unless the lower bound is strengthened.

**CONJECTURE C2-C (unknown-onset monitoring floor).** For a monitoring spec requiring detection within `ell` of *every* onset in a horizon `H_R`, any policy under the pathwise cap needs
`BR >= c0 (H_R/ell) log(1/gR)/kR` (up to the adaptivity gain of two-stage sampling, which can lower the per-window cost from `m_R` to a first-stage cost of the same
order `1/kR` times a constant but not below it). Why it is not proved: the per-window information bound controls `E_{nu_j}[N_j]` (alternative measure), while the pathwise cap
controls `sum_j N_j` under every measure; summing over windows needs a change-of-measure on the first trigger (Lau-Tay's two-stage design is the relevant upper-bound structure; Geng et al.'s
sampling-rights recursion is the relevant exact solution of the single-change Bayesian version; both audited). If this floor holds, the combined frontier is
`B >= klP/kP + (1-gP)(H_R/ell) c0 log(1/gR)/kR` and the fixed split `rho* = (klP/kP)/(klP/kP + (H_R/ell) c0 log(1/gR)/kR)` is tight to a constant in the guarantee regime.

### 2.4 Optimal split scaling and when an adaptive split strictly beats every fixed split

Two regimes must be kept apart.

**Guarantee regime (B near the frontier).** Specs are thresholds: the monitor either meets its spec (needs `>= R*` rights) or does not. Then an adaptive recycling
split gives nothing over a fixed split. *Proposition C2-S0 (PROVED).* If the monitoring value is `V(r) = v 1{r >= R*}` and the promotion requirement is the same,
the best adaptive policy and the best fixed split `(BP, BR) = (B - R*, R*)` have equal value, because the only constraint binding on the adaptive policy is `N^req <= B - R*` on promotion paths,
which is exactly the fixed split. The optimal `rho* = (B - R*)/B`. This also explains the repo's exact `(2,1)` match on the registered `T=6, B=3, d=1` cell.

**Utility regime (B above the frontier).** Let the objective be `E[A(pi) + 1{promote} V(B - N^req)]` with `V` nondecreasing and the promotion-policy class closed under truncation.

*Proposition C2-S1 (PROVED).* `J_adaptive >= max_{BP} J_fixed(BP)`, and equality holds iff some optimal adaptive policy has, for some `BP*`, `N^req <= BP*` on promotion paths and
`V(B - n) = V(B - BP*)` for every promotion count `n` with positive probability. In particular, if `V` is strictly increasing on the relevant range, adaptive strictly beats every fixed split
iff every optimal adaptive policy has a non-degenerate promotion-count distribution (at least two distinct values `n1 < n2` each with positive probability among promotion paths).
*Proof.* (<=) Taking `BP*` the fixed-split class contains the optimal adaptive policy and credits `V(B-BP*)`; if `V(B-n)=V(B-BP*)` a.s. the values coincide. (=>) Suppose a fixed split attains `J_adaptive`
with policy `pi'` and split `BP*`. Evaluated adaptively, `pi'` earns `J_fixed(BP*) + E[1{prom}(V(B-N)-V(B-BP*))] <= J_adaptive`, forcing the second term to be zero; strict monotonicity then gives `N = BP*` a.s. on promotion paths. QED.

This is policy-class bookkeeping, consistent with the repo's closure of the label-purpose wrapper; it identifies *when* headroom exists, not a new algorithm.

*Heuristic scaling (NOT proved; Gaussian-LLR approximation).* With LLR drift `kP`, variance `2kP` and boundary `a`, promotion power at sub-cap `x` is `Phi((kP x - a)/sqrt(2 kP x))`.
Minimizing `G * (1 - power(x)) + (monitoring loss)(B - x)` gives `x* ~ (a + z sqrt(2a))/kP` with `z ~ sqrt(4 log B)` (stationarity of the Gaussian tail against a `1/(B-x)` monitoring
loss), i.e. `rho* ~ [a + 2 sqrt(2 a log B)]/(kP B) -> 0`. The adaptive-minus-fixed relative gap is of the same order as `rho*` (the leftover `BP* - E[N]` is `~ z sqrt(2a)/kP`),
so it vanishes as `B` grows but is largest at moderate `B` where the first-passage tail is heavy.

### 2.5 R2 / R6 checklist for C2

| Source | Check | Expectation |
|---|---|---|
| Geng-Bayraktar-Lai (audited), Lau-Tay (audited), Huang-Veeravalli finite-horizon QCD (audited), Shin-Ramdas-Rinaldo e-detectors (audited) | Monitoring half: do they state finite-sample (not asymptotic) delay/false-alarm/budget results for a hard cap on samples under unknown onset? If yes, the monitoring half of C2-A/C2-C is covered | Likely covers single-change, immediate-feedback versions; delay and hard pathwise cap with deadline not stated |
| Li et al. active two-sample / usage-constrained (audited), Chick et al. (audited) | Promotion half | Covers IID, immediate (Li) or Bayesian one-switch (Chick) |
| Episode alpha spending / online FWER (audited) | R6 baseline for the promotion half; also the fixed-split baseline composition with CUSUM | Is the baseline the frontier must be compared with |
| Gong-Zhang, Qiu, Ryabchenko, DAL, Braverman pacing | Confirm none states a budget-split frontier between two risk-controlled phases | No |
| Repo internal: tagged-allocation equivalence, `(2,1)` match | Any claimed advantage over fixed split is policy-class headroom unless a structural bound is proved (C2-S1 says exactly when) | A frontier *theorem* survives; a wrapper does not |

---

## 3. C3 note: computational separation for the first-promotion solver

What would make the exact first-promotion XP solver a *setting* contribution under R2 is a **hardness or size separation showing the XP shape is intrinsic**, not an accident of the
representation. Candidates:

1. **Size of the generic formulation (trivial, PROVED but weak).** The registered count `N_N(T,B) = sum_{j<=B} binom(T,j) 3^j >= binom(T,B) 3^B` shows the null-tree formulation is `Omega(T^B/B!)`,
   hence not FPT in `B`. This describes the algorithm's formulation only; it is not a lower bound on the problem, so it is not a separation.
2. **Where absorption matters (clarification).** First-promotion absorption lets the continuation be a single-agent belief DP (`O(T N_L K^2 4^B)`). It is *not* what makes the null tree polynomial for fixed `B`: the
   learner's information histories are determined by query tape and released outcomes even without absorption (at most `O(T N_L)` many). What absorption removes is the need to carry the *adversarial null* past
   promotion. A representation that does not absorb (risk event depends on post-promotion behavior) has a null policy space still keyed by learner histories, so the sequence-form size is not obviously exponential in `T`
   for fixed `B`; it is exponential in `B`, and in `T` only when `B = Omega(T)`. I could not justify the statement "exponential in T without absorption" for fixed `B`; the repo's phrasing should be read for `B` growing.
3. **W[1]-hardness or ETH-type bound in `B` (CONJECTURE).** Show that deciding whether a value/risk pair is achievable for the declared contract with `K`, `d` fixed, parameterized by `B`, is W[1]-hard (or
   has no `f(B) poly(T)` algorithm under ETH). Natural route: reduce a subset-selection problem (choose `B` query times from `T` to separate hypotheses; known-HMM sensor scheduling is a candidate source of hardness;
   *needs source check*) to the budgeted design problem with `alpha` close to 1 (so the safety side is vacuous). A reduction must encode the combinatorial structure in the HMM's transition matrix and
   in query-time-dependent informativeness; I do not have a cheap construction. The adaptive version could be harder but also admits the same belief DP, so XP membership is the upper side.
4. **Hardness of compact policies (CONJECTURE).** A growing family where every risk-preserving finite-state controller with `m` memory states has cost gap `>= epsilon(m)` against the full-history optimum. The repo's
   posterior-alias counterexample is a finite instance; a family would turn the "compression is impossible" branch of `switching_delayed_pomdp_information_state_audit_v1.md` into a theorem.

**Is it provable cheaply? No.** Items 3-4 each need a nontrivial reduction or family; none is a one-day exercise, and the relevant robust/multi-environment POMDP complexity results (Brice et al., Bovy et al.) are
log-only in the audits I read (the first-promotion doc says they were compared at source level, but I did not see their complexity classes), so they could already contain the hardness side.
Recommendation: do not pursue C3 as a contribution; keep the solver as the R1 oracle for cells where it is solvable.

---

## 4. Which target is strongest

1. **C1 (b)+(c) as a quantitative promotion-delay frontier for delayed capped HMM observation (drop-V flavour, see R3 screen).** Strongest because (c) is proved, (b) has an explicit nontrivial step
   (filter forgetting + concentration under dependence), C1-D1 gives an in-repo separation, and Conjecture C1-E (persistence-aware querying) is a candidate rate-level separation from calendars.
   Key assumption: finite, well-specified, uniformly ergodic, identifiable HMM family with bounded emissions. The honest weakness is that the model-conditional guarantee is weaker than the repo's causal null.
2. **C2 frontier.** (a) lower bound proved but a standard sum; upper bound proved only for the promotion half; unknown-onset monitoring floor is an open conjecture; the adaptive-vs-fixed characterization is policy-class bookkeeping.
3. **C3.** Not provable cheaply.

## 5. Scratch numerical checks (outside the repo; not evidence of efficacy)

Scripts: `C:\Users\nigel\AppData\Local\Temp\claude\C--Users-nigel--claude-spares-spare-HQYN75\6eec0303-54f7-4457-a727-0b093e7dee97\scratchpad\c1_iid_check.py` and `...\c2_split.py`.

**5.1 IID calibration of Prop. C1-C (K=1).** `eps=0.1` (Ber(0.6) vs Ber(0.5)), `kappa=0.020136`, `alpha=0.05`, `gamma=0.2`: lower bound `kl(0.8||0.05)/kappa = 94.7` labels; exact Neyman-Pearson (non-randomized) needs 158;
the anytime LR e-process needs about 220 (Monte Carlo, 1e5 sims, grid step 5). Constant-factor gaps, as predicted.

**5.2 C2 split (stylized Monte Carlo; not the two-law oracle).** Parameters: `alpha=.05` (`a=3.0`), `kP=.05`, `kR=.1`, `gP=gR=.2`, `beta=.05`, `d=5`, horizon `n=3000`, reversal hazard `2/n` per round, 1 unit benefit/round.
Frontier numbers: `klP = klR = kl(.8||.05) = 1.906`; promotion floor `38.1` labels, monitoring floor `19.1`, sum floor `57.2`; with the `(1-gP)=0.8` weight of Theorem C2-A it is `38.1 + 0.8*19.1 = 53.4`.
LLR first-passage (Gaussian increments, 20000 paths): mean 63.6, q10 20, q50 49, q90 125, q99 248 labels. Monitoring: periodic calendar with spacing `ceil`-free approximation `d + m H/r`, `m = ceil(a/kR) = 30`.
Utilities (fixed split optimized over `BP`; adaptive = promotion allowed with `N <= B - R*`, monitor receives all leftover rights; `R*=20`):

| B | best fixed `rho*` (`BP*`) | J fixed | J adaptive | gap | gap/J |
|---|---|---|---|---|---|
| 100 | .80 (80) | 1258.7 | 1344.4 | 85.7 | 6.8% |
| 150 | .87 (130) | 1529.8 | 1941.4 | 411.6 | 26.9% |
| 200 | .52 (104) | 1828.4 | 2279.8 | 451.5 | 24.7% |
| 300 | .50 (149) | 2284.3 | 2578.3 | 294.0 | 12.9% |
| 500 | .42 (209) | 2618.6 | 2750.5 | 131.9 | 5.0% |
| 700 | .37 (257) | 2735.8 | 2807.7 | 71.9 | 2.6% |

Reading: `rho*` decreases in `B` and the adaptive-fixed gap is strictly positive and shrinks, as Prop. C2-S1 and the heuristic scaling predict (the heuristic formula gives `rho*~.44` at `B=700` versus `.37`
observed: right order, not an accurate prediction). Monte Carlo error is of the order of 1% of J; the model is a stylized proxy and the gap sizes should not be quoted as findings.

## 6. Continue / pivot / stop

- **C1: CONTINUE** on theory only, scoped to Proposition C1-C (done), the filter-forgetting lemma and concentration step for (b), and a small exact enumeration confirming C1-D2 and the budget separation C1-E in a two-regime cell. Gate before any prototype: read Arnold et al., Emmenegger-Mutny-Krause and Kapoor-Nair at theorem level (R2).
  Stop signal: if Arnold et al. or an HMM-filter confidence-set paper already gives an exclusion rate under delayed predictable sampling, C1 reduces to a baseline again.
- **C2: PIVOT** to a supporting frontier section (Theorem C2-A, Prop. C2-S0/S1). Only continue it as a headline if Conjecture C2-C (unknown-onset floor) is proved and the monitoring half is shown not to be a source theorem (Geng, Lau-Tay, Huang-Veeravalli).
- **C3: STOP** as a standalone contribution (no cheap hardness proof; keep the solver as the R1 oracle).
