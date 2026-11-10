# 06 Theorem ledger (workstream B; other workstreams append their own sections)

Statuses: PROVEN (proof in file) / NUMERICALLY_CHECKED / CONJECTURE / FAILED. "Closest prior" is from memory or
repo docs and was NOT retrieved/verified unless stated.

## Common setting
Rounds t; paired score Z_t in [-1,1] with mean mu_t (independent across t given the path; mu may be predictable).
Class C(v,J,hd): |mu_{t+1}-mu_t| <= v except on jump steps (<= J, J>=v), jump steps >= hd apart. A request at s is
released at s+d; decision at tau uses labels requested at s <= tau-d; at most B requests (pathwise, booked at
request); the query rule may depend on released labels and private coins only. Estimand: hold-for-h payback
P_tau = sum_{j<h} mu_{tau+j} - k. Filtration F_tau = (released labels, own coins). A certifier is alpha-valid if
for every path in C and every (possibly adaptive) choice of tau, h: Prob(certify and P_tau <= k) <= alpha.
drop(a) = J ceil(a/hd) + v(a - ceil(a/hd)) (max decrease over a steps); slack
S(d,h) = (1/h) sum_{j<h} drop(d+j) (= v(d+(h-1)/2) for pure drift); L = mean level; gamma = L - k/h - S.
Rademacher labels (P(Z=1)=(1+mu)/2) lie in [-1,1]; lower bounds are for that subfamily.

## T0  Reversal impossibility (exact, finite)  -- PROVEN + NUMERICALLY_CHECKED
Two worlds with identical history law (means agree on every request time <= tau-d), one with payback > 0 and one
< 0: every rule has type I + type II = sum_h min(p+(h),p-(h)) = 1. Exact rational enumeration with an adaptive
query rule and brute force over all 2^|H| deterministic rules (`test_exact.py`). One visible differing label gives
a strictly smaller sum. Closest prior: `docs/switching_current_regime_evidence_v1.md` (same argument). NOT new.

## T1  Irreducible slack  -- PROVEN
Any alpha-valid certifier (alpha<1) has Prob(certify at tau) <= alpha in every world whose history through request
time tau-d is the prefix of some path in C with P_tau <= k. In particular a constant world L is certifiable with
probability > alpha only if L - k/h > S(d,h), whatever B and the noise level (even noiseless, B = inf).
Proof. The history law depends only on (mu_s)_{s<=tau-d} and the query kernel. Take the completion that drops at
the maximal rate allowed by C from tau-d; by monotonicity of the greedy drop its horizon sum is h L - sum_j
drop(d+j) (no clipping at -1), which is <= k iff L - k/h <= S. That world is in C, is a null for the (tau,h)
event, and has the same history law as the constant world, so validity bounds the certification probability of
both by alpha. QED. Brute-force check of drop(a) over all integer paths: `test_envelope_theory.py`. Clipping
needs v(h-1)/2 <= 1 + k/h for the stated formula.
Closest prior: bounded-drift envelope in `switching_problem_v1.md` and the mechanism screen; the J,hd extension is
elementary. If a jump of size >= gamma is admissible just before the last label, no certificate exists (T5).

## T2  Statistical lower bound with budget B and drift v (pure-drift class, Rademacher)  -- PROVEN; NUMERICALLY_CHECKED (tight within 2.4x)
Let kappa = kl(1-beta || alpha) (binary KL). If an alpha-valid certifier with <= B requests certifies the constant
world L = gamma + k/h + S with probability >= 1-beta, then
   sum_{m=0}^{B-1} KL( Rad(L) || Rad(L - (gamma - v m)_+) )  >=  kappa.        (*)
gamma_lb(B,v,alpha,beta) = smallest gamma satisfying (*). Consequences: gamma_lb ~ sqrt(2 kappa/B) when v B << gamma
(v=0); gamma_lb ~ (6 v kappa)^{1/3} once B >= gamma/v, so the budget saturates at B_sat ~ (c/v)^{2/3} (nothing beyond
it helps); d, h, k enter exactly through L - gamma = k/h + S.
Proof. Null P-: mu-_{tau-d-m} = L - (gamma - v m)_+ for m>=0 and mu-_{tau-d+i} = L - gamma - v i for i>0. Every
step is <= v in absolute value, so P- is in C. Its horizon average is L - gamma - v(d+(h-1)/2) = k/h, so P_tau(P-) = 0
<= k and validity gives P-(cert) <= alpha. P+ = constant L is in C with P+(cert) >= 1-beta. The chain rule for
adaptive experiments gives KL(P+ hist || P- hist) = E+ sum over requests of KL_i, the request at round s contributing
KL(Rad(L)||Rad(mu-_s)) (query kernels coincide). KL_i decreases in the age m, and requests are distinct rounds
<= tau-d, so B requests contribute at most the sum in (*). Data processing on {cert}:
kl(1-beta||alpha) <= kl(P+(cert)||P-(cert)) <= KL(hist). QED. Assumes |L|<=1 and no clipping.
Exact Neyman-Pearson on the pair (B<=14, 8 cells): gamma_lb <= gamma_NP <= gamma_ub (tests).
Closest prior: Le Cam two-point + variation-budget tracking lower bounds (Besbes-Gur-Zeevi; the v^{1/3} rate and
the window bias-variance trade-off are textbook); repo `switching_noisy_information_lower_bound_v1.md` (same
binary-KL data-processing, hidden-onset pulse, no drift, no horizon average). Different functional, same technique.

## T3  Achievability: B2 (time-uniform, adaptive batch, delay, reserved budget)  -- PROVEN (validity); NUMERICALLY_CHECKED (rate)
(a) Validity. Batch b commits at a predictable time r_b (n_b is F_{r_b}-measurable); S^b_m = sum_{i<=m}(Z - mu) over
its first m labels is a martingale with 1-sub-Gaussian increments (range 2; the query decision precedes the
outcome). M_m = sqrt(rho/(m+rho)) exp(S_m^2/(2(m+rho))) is a nonnegative supermartingale with M_0 = 1 (Fubini over
the Gaussian mixture), so P(exists m: |S^b_m| >= u(m)) <= alpha_b with
u(m) = sqrt((m+rho)(ln((m+rho)/rho) + 2 ln(1/alpha_b))). Union over b with alpha_b = alpha/(b(b+1)). On the
simultaneous event, for every arrival time, h and batch,
sum_{j<h} mu_{tau+j} >= h (Zbar_m - u/m) - (1/m) sum_i sum_{j<h} drop(tau + j - s_i)
since |mu_{tau+j} - mu_{s_i}| <= drop(tau+j-s_i). Certifying when this exceeds k is alpha-valid under arbitrary
stopping, arbitrary (tau,h,batch) selection, delay d and request-time reservation, and for predictable mean paths.
Requires an honestly declared class C. NUMERICALLY_CHECKED: exact DP crossing probability <= alpha on 18
(alpha, mu0, m*) cells to M=1500 (.0169 at alpha=.05, M=5000); MC with adaptive h-grid on tight adversaries
(null_flat, null_decline:40/100) <= alpha (N=150 each; oblivious adversary).
(b) Rate. A window of the n latest labels certifies the constant world w.p. >= 1-beta when
gamma >= [u(n) + sqrt(2 ln(1/beta) n)]/n + v(n-1)/2. Optimising n <= B gives gamma_ub;
gamma_ub/gamma_lb is 1.75 to 2.65 over alpha=.05, beta=.2, v in {0,.002,.01}, B in {50,200,1000} (single-batch
Hoeffding: 1.75-2.4, 1.75 in the v^{1/3} regime). So the frontier matches up to a constant ~2-3 in B and v and
exactly (additively) in d, h, k.
Closest prior: Howard et al. 2021 and Waudby-Smith-Ramdas confidence sequences; windowed CS with drift bias
(whether one source states exactly this form is unverified); mechanism screen (fixed-n version). Routine combination.

## T4  Optional-continuation counterexample  -- PROVEN (exact computation)
World mu = k/h = .1 (payback exactly 0). Certify when Zbar_m - sqrt(2 ln(1/alpha)/m) > k/h at ANY look m <= M.
Exact DP (agrees with rational arithmetic to 1e-12), alpha = .05: P = .0084 (M=10), .0501 (100), .0929 (1000),
.1221 (5000), versus a single pre-committed look < alpha. Gaussian-naive (z=1.645): .119 (10), .280 (100),
.482 (5000). B2 on the same worlds: <= .0169. So the B1 envelope is valid only at predeclared completion times
(as the mechanism screen says); adaptive batch size/stopping needs T3(a). Closest prior: sequential analysis
(peeking). Not new; it motivates, it is not a result.

## T5  Persistence alone does not give a payback certificate  -- PROVEN (T1 with J); NUMERICALLY_CHECKED
If abrupt changes of any size are allowed (J >= 2L), a dwell time hd of any length leaves S >= J >= L for every
horizon touching an unobserved round, so no positive-payback certificate exists. Flip stress (half-period 100, the
coordinator's E case; dev pilot, N=300): drift-class certificates (B0, B1, B2 with declared v) certify wrongly in
20-60% of runs (P(wrong | cert) ~.7-.8, realised net -10 to -18 per stream for B0a/B0w/B1/B1n/B2); B2 with the honest
class (J=1.8, hd=100) refuses (0 certifications). Consistent with E_RESULTS (89% promoted, .81 promoted-and-
nonpositive). Regime-flip validity of an e-process gate is historical, not forward.

## T6  Price of time-uniformity / multi-attempt lower bound  -- CONJECTURE
Any certifier valid for all tau (or K attempts) needs gamma larger by an additive Theta(sqrt(ln ln n / n)) or ln K term
beyond (*) (LIL-type lower bound); B2's ln((m+rho)/rho) is the matching upper-bound term. Not proved.

## T7  Statistical lower bound for the jump class (J, hd)  -- CONJECTURE
Expected: (*) with the differences replaced by the best placement of one jump inside the labelled window. Not derived.

## T8  Variance-adaptive (Bernstein / betting) frontier  -- CONJECTURE (not implemented)
Range-based bounds are conservative for 0/1-loss differences with a small disagreement rate; gamma should scale with
the standard deviation in both bounds. Needed for non-vacuity at realistic Delta: with +/-1 labels, v=.002, B=150,
h=30 the certificate needs L ~ .45 or more.

## FAILED / refuted
* "A naive fixed-n Hoeffding certificate stays valid under optional continuation": FAILED (T4).
* "A dwell-time assumption suffices to certify future payback": FAILED unless jump size is bounded (T5).
* "B1 as a post-hoc certifier is economically useful": dev pilot shows late/stale certification (delay ~120 rounds).

## Verdict on novelty
T1-T3 are correct and give a frontier within a constant ~2-3 in (B, v), exact in (d, h, k): matching bounds in all of
B, d, h, k, v, with an achievable certificate and an optional-continuation counterexample, so the reviewer's
survival condition is met formally. But T1 is the repo's bounded-drift nonidentifiability, T2 is Le Cam + the
variation-budget bias-variance trade-off (known rate) in repo-style binary-KL data processing, and T3 is a
confidence sequence with an age-bias term. No new technique. Verdict: mostly reduces to prior work (ALREADY_COVERED
as a headline theorem); supportable as a short proposition plus the counterexample and the flip stress. Not verified
against retrieved literature.
