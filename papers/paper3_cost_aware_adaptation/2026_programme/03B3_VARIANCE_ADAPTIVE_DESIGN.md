# 03B3 Variance-adaptive payback certificate B3 (design, written BEFORE any real-data run)

Status: development. Code `src/shiftlab/paper3/payback/variance_adaptive.py`, tests
`tests/paper3/payback/test_variance_adaptive.py`, scripts `scripts/paper3/payback/b3_*.py`, outputs
`outputs/paper3/payback/b3/`, ledger `ledger/payback.jsonl` (kind `B3_*`). Results: `B3_RESULTS.md`.
Everything on c4 is DEVELOPMENT (all streams exposed). Validity statement below is **PROOF_SKETCH (not audited)**.

## 1. Why B2 is vacuous on c4 (pre-run analysis, even episodes only)
B2 certifies iff `h*(Zbar - u/m) - window_drift_term > k`. Two separate losses of power:
(i) the range-based radius u/m (sub-Gaussian-1), which variance adaptivity can fix, and
(ii) the irreducible slack of T1: `k/h + S(d,h)`, `S = v(d + (h-1)/2)`. For the c4 contract d=100, v=.002, h=100,
k=3: hurdle = .03 + .2990 = **.329** on the mean of Z. Descriptive marginals on EVEN episodes (27 streams, 1,089
episodes): the stream mean of Z over the first 150 rounds ranges -.04 to +.24 (dc_311 .24, sf_311 .22, dallas_animal
.15); only 2.8% of episodes have a first-150-round mean > .33 (sf_311 30%, dc_311 26%, pittsburgh/dallas_animal/kc a few %).
So under the declared class no certificate whatsoever (even with exact knowledge of the label mean over the
queried window, B = infinity) can certify most episodes at h=100 (and h in [20,200] has hurdle >= .31): this is T1,
not a property of B2's radius. B3 can recover at most the radius part. This is pre-registered as the expected outcome:
**B3 should certify in a small fraction of episodes on c4 at v=.002, concentrated in sf_311/dc_311.**
(Empirical check of the declared v: median over episodes of the max 100-lag change of the 100-round rolling mean of Z,
divided by 100, is .0008-.0036 per round across streams, i.e. v=.002 is realistic or optimistic, not conservative.)

## 2. Mechanisms
### M1 variance adaptivity (implemented, `B3Certificate`)
Per batch b a predictable-plug-in empirical-Bernstein lower confidence sequence (Waudby-Smith and Ramdas, 2024,
JRSS-B, "Estimating means of bounded random variables by betting", PrPl-EB; the formula and the psi_E/4 fix follow the
port `src/shiftlab/paper3/atlas/certificate_stops.py::PrPlEBCS`). Differences from that port, both required here:
(a) ONE-SIDED (threshold 1/alpha_b, not 2/alpha_b); (b) NO running intersection of lower endpoints: the intersection
is valid only for a constant mean; under drift the CS is for the lambda-weighted average of the conditional means at
the current prefix, so we use the endpoint at the current prefix only.
W_i = (Z_i+1)/2 in [0,1]. lambda_i = min(sqrt(2 ln(1/alpha_b)/(sigma2hat_{i-1} i ln(1+i))), lam_max),
mu_hat_i = (1/2 + sum W)/(i+1), sigma2hat_i = (s0 + sum (W-mu_hat)^2)/(i+1) (s0 = prior_var, default 1/4),
v_i = 4(W_i - mu_hat_{i-1})^2, psi_E(l) = (-ln(1-l) - l)/4.
Lower endpoint for the weighted average: lo_m = (sum lam_i W_i - sum v_i psi_E(lam_i) - ln(1/alpha_b)) / sum lam_i.
Drift: weights w_i = lam_i/sum lam; `lcb_sum(t,h) = h*(2 lo_m - 1) - sum_i w_i F(t - s_i)`, `F(a) = sum_{j<h} drop(a+j)`
(envelope as B2). Variants: `mode="batch"` (alpha_b = alpha/(b(b+1)) per committed batch, as B2) and
`mode="single"` (one CS over all labels in request order, full alpha, no batch union; also covers later batches
because they are just further elements of the same predictable sequence).
### M2 disagreement gating (implemented for synthetic only, `B3GatedCertificate`)
**Observability finding.** In the core contract `PublicEvent.disagreement = deployed_action != reference_action` is
public before the label decision (`src/shiftlab/contract/interface.py:56-57`; `baselines.py:100` returns propensity
0 on agreements; `harness.py:101`, `:118` cost is 0 on agreements), and the c4 builder
(`../shift-research-starter/scripts/qsg_methods_search/c4_build.py:121-132,163-164`) defines losses
`l_k = (m_k.predict(X) != y)` of two frozen models, so true disagreement `p0 != p1` is a function of public x and
frozen models, hence observable at decision time. BUT the sealed npz arrays contain only `l0, l1, starts, delay`, not
predictions. The only recoverable indicator is `l0 != l1` (Z != 0), which is a strict subset of true disagreement
(both wrong with different predictions gives Z = 0 yet disagreement) and is **label-dependent**, so it is NOT
observable at decision time. The transfer simulator (`src/shiftlab/paper3/transfer/sim.py:59`, `gru.py:60`) uses
`dis = l0 != l1` as if public; that is an evaluator-side proxy and is not carried over here. **Decision: M2 is not
used on c4.** A valid c4 use needs regenerating predictions via `c4_build.py` (not done; raw data/model refits out of
scope here). M2 is implemented and validated on synthetic streams where the indicator D_t is generated explicitly.
Construction: the sequence is ALL rounds of a window (agreement rounds contribute Z=0 with no label; a queried
disagreement round contributes its label released at s+d). Query rule: propensity 1 on D_t=1 while budget remains,
0 on D_t=0 (predictable given public x_t). Because every round of the usable prefix has a known Z, no selection bias
arises; the PrPl-EB CS runs over rounds in order on the unconditional conditional means mu_t = E[Z_t | past]; the class
(drift of mu_t) is exactly B2's. The usable prefix at time t is rounds r..e with e = (earliest queried-but-unreleased
round) - 1. Budget B buys B disagreement labels so the window extends to about B/p_dis rounds; variance falls with p_dis.
`mu_t = p_dis m_t` needs no separate estimate of p_dis. (Truncating the window when the budget is exhausted only
chooses which prefix is read; the CS is simultaneous over all prefixes.)
### M3 drift slack and alpha spending
Same class C(v,J,hd) as B2. Modes `batch` and `single` ablated (section 5).

## 3. Validity proof sketch  [PROOF_SKETCH, not audited]
Filtration: G_i = sigma(all outcomes Z_1..Z_{i-1} in request order of the batch, including labels not yet released,
all covariates and private coins up to the request of i; for M2 additionally D_i). Request i of batch b has
omega_i = E[W_i | G_{i-1}] = (1 + mu_{s_i})/2 where mu is the (predictable) mean path in C. The query decision for i
(and batch commitment, n_b) is G_{i-1}-measurable (depends on released labels and coins only; M2: on D_i and public x).
Under constant delay d the released labels at t are a prefix in request order (so the prefix index m is a valid
G-time at which to read the CS; proof of B2 needs the same non-adaptive delay).
Plug-ins mu_hat_{i-1}, sigma2hat_{i-1}, lam_i are functions of W_1..W_{i-1}, hence G_{i-1}-measurable (computed
retrospectively by the certifier once the prefix is released; no requirement that they be available at request time).
Supermartingale: for lam in [0,1), xi = W - mu_hat >= -1, `exp(lam xi - xi^2 (-ln(1-lam) - lam)) <= 1 + lam xi`
(Fan, Grama, Liu 2015); conditional on G_{i-1}, E[1 + lam(W - mu_hat)] = 1 + lam(omega - mu_hat) <= exp(lam(omega - mu_hat)).
Hence M_m = prod_{i<=m} exp(lam_i(W_i - omega_i) - v_i psi_E(lam_i)) (with v_i psi_E = (W_i - mu_hat)^2(-ln(1-lam)-lam))
is a nonnegative G-supermartingale with M_0 = 1, valid for ANY (time-varying, predictable) omega_i. Ville:
P(exists m: M_m >= 1/alpha_b) <= alpha_b. On the complement, for all m,
sum lam_i omega_i > sum lam_i W_i - sum v_i psi_E - ln(1/alpha_b), i.e. weighted-average lower bound lo_m.
Union: alpha_b = alpha/(b(b+1)) (batch mode, sum = alpha) or one sequence with alpha (single mode; the sequence is
the concatenation of all queried labels in request order, whose query decisions are predictable, so one supermartingale).
Drift: on the good event, for every arrival time t, hold h and prefix m, `|mu_{t+j} - mu_{s_i}| <= drop(t+j-s_i)` gives
sum_j mu_{t+j} >= h*(2 lo_m - 1) - sum_i w_i F(t-s_i), simultaneously, so certification at any data-dependent (t,h,m),
optional continuation, adaptive batch choice are covered; error <= alpha for every path in C (including predictable
adaptive adversaries). If a query propensity q_i < 1 were randomised, the unqueried round contributes no increment and
the sequence index is the queried subsequence; the propensity is a coin independent of Z given G_{i-1}, so the
subsequence is still a martingale (here q in {0,1} predictable; no HT weighting is used, hence no 1/q inflation).
Caveats: validity only relative to the declared class (T5); non-adaptive delay; M2 requires that D_t is determined
before Z_t is revealed and that the class constrain mu_t = E[Z_t | past] (not the conditional mean given D).

## 4. Development protocol (fixed now)
### 4a. Synthetic validity (before any real run)
Seeds `SeedSequence([5301600000, class_idx, i])`, i < N, N = 1000 per class (dev block, disjoint from pilot1's 5301500000).
Setting: T=400, B=150, d=5, h=30, k=3, alpha=.1, declared v=.002 (pilot1 setting, `sim.Spec`).
Classes: pilot1 `null_flat`, `null_decline:60` (+/-1 Rademacher), and sparse classes `sparse_null_flat`,
`sparse_null_decline:60` with disagreement rate p in {.15, .30} (D_t ~ Bern(p), Z = D*(+/-1), mean path E[Z]=mu_t so
that the same tight nulls apply; m_t = mu_t/p), rate range chosen from the even-episode P(Z!=0) marginals (.04 to .43,
median .11; p is a disagreement rate >= P(Z!=0)). Wrong-sign certification rate with Wilson 95% CI must be <= alpha=.1
(requirement: the Wilson UPPER bound need not be <= .1, but a point estimate above .1 or a lower Wilson bound above .1
is a failure; both are reported). Optional-continuation counterexample: world mu = k/h = .1, Rademacher and sparse
(p=.3), no drift term (v=0), looks m <= M in {10, 100, 1000}, alpha in {.05, .1}, MC N=2000 (B3 is not a threshold
rule so no exact DP); compare with Gaussian-naive.
In-class power/delay vs B2: pilot1 `drift`, `boundary`, `dwell` (+/-1) and sparse in-class (mu = p*g_t) with p in {.3,.45}.
Also records certification rate, mean delay, mean labels, mean realised net.
### 4b. Real (c4) development on EVEN episodes only (episode index even, 0-based)
Fixed configuration grid (the whole tuning budget, 5 configs, h=100, c_q=0, v=.002, alpha=.1, d=stream delay):
 C0 batch, sigma_plan=1 (plan as B2), lam_max=.5; C1 batch, sigma_plan=.1; C2 batch, sigma_plan=1, lam_max=.75;
 C3 single, sigma_plan=1, lam_max=.5; C4 single, sigma_plan=.1, lam_max=.75.
Selection rule (fixed): highest stream-equal-weight mean realised net per even episode; ties (including all-zero) go to the
lowest index. `sigma_plan` rescales the radius term in the batch-size plan `plan_batch_size`-style objective
sqrt(2 ln(1/alpha_b) sigma_plan^2/n) + mean drop. M2 is not used on c4 (section 2).
### 4c. Real confirmation-style evaluation on ODD episodes, once
Chosen B3 (v=.002) evaluated once on odd episodes: h=100 primary, c_q=0 primary, c_q=.05 secondary (h=50 also run).
Endpoints exactly as R1: realised net payback per episode; stream-cluster bootstrap 10,000 resamples, equal stream
weights, seed 20261110; contrasts B3-B0a, B3-B0w, B3-B0b, B3-B2; certification rate, wrong-sign fraction among
certifications (realised hold sum - k <= 0), delay, labels. B0a/B0w/B0b/B2 on odd episodes are taken from the R1
per-episode table (`outputs/paper3/payback/real_r1/per_episode.csv`, same driver, same parameters; read-only).
Pre-registered secondary sensitivity (fixed now, not chosen from results): the same B3 config and B2 re-run on odd
episodes with declared v in {.0005, .001}. These are NOT in the declared class of the primary; validity is only
conditional on the declaration being true, and the realised wrong-sign fraction is reported as the cost of the
declaration. They answer "how much of the vacuity is the declared slack".
Secondary: B3 as a switching rule vs the Paper 1 Wald+cutoff reference
(`src/shiftlab/paper3/baselines.py`): attempted only if its interface accepts the c4 loss streams without changing
its contract; contract differences (J-table costs, multi-switch, reference-policy deployment vs single switch with a
payback certificate) will be stated; otherwise reported NOT RUN.
### 4d. Interpretation rules
Validity table failing => B3 variant rejected regardless of power. A B3-B2 improvement is judged from the CI; B3-B0x
as in R1. Nothing here is confirmatory.
