# 06 Proof audit, workstream B (payback certification)

Label: MANUAL_FALLBACK. Same model family as the author workstream (no cross-model reviewer backend available), so this is
NOT a cross-model independent audit. Auditor read ledger 06, design 03B, `src/shiftlab/paper3/payback/*.py`, reran
`tests/paper3/payback` (13 pass, 32 s), and wrote `scripts/paper3/payback_audit/audit_checks.py` (A: UB/LB grid, B: independent
T4 DP, C: T1 clipping search). Note: results dir is `2026_programme/results/payback/` (frontier.json read).

Retrieved sources (abstract level only, no full text read): Besbes-Gur-Zeevi arXiv 1405.3316 (abstract states variation budget
is linked to minimax regret; explicit rate NOT on page, so the v^{1/3} rate comes from memory); Howard et al. arXiv 1810.08240
(abstract: time-uniform nonparametric CS, sub-Gaussian/normal-mixture-type boundaries); web search snippets only for Chugg-Ramdas
"closed-form empirical Bernstein CS" (arXiv 2512.21300; per snippet gives a CS for the average conditional mean allowing drift),
arXiv 2302.14248 (time-uniform CDF bands for running averaged conditional distribution under nonstationarity), arXiv 2311.08168.
Waudby-Smith-Ramdas betting CS, age-bias literature, and quickest detection with sampling constraints were NOT retrieved.
Prior-art conclusions below are therefore provisional.

## Per-theorem verdicts

### T0 reversal impossibility: VERIFIED (trivial)
Claim: two worlds with equal history law force min(typeI+typeII)=sum_h min(p+,p-)=1 (= 1 - TV = 1). Proof is the identity
inf_rule (P+(reject)... ) = 1 - TV(P+,P-); with TV=0 it is exactly 1 for adaptive query rules because the history law
(product of query kernel and label kernels) coincides. No gap. Nit: validity requires typeI<=alpha hence typeII>=1-alpha;
state it that way. Content is a restatement of TV=0; it is not a theorem of any strength.

### T1 irreducible slack: GAP (fixable)
Steps checked: history law depends only on (mu_s)_{s<=tau-d}; constant history admits the max-rate-drop completion (jumps at
step 1, 1+hd, ...; hd-separation respected because the past is constant); drop(a) formula correct (J*ceil(a/hd)+v*(a-ceil)).
Gap: clipping. The stated sufficient condition "v(h-1)/2 <= 1+k/h" does not prevent clipping (counterexample v=.01, d=300, h=3,
k=0, L=.6: condition holds, yet L - v(d+h-1) = -2.42 < -1, so the null path leaves [-1,1] and is not in C as written). A random search
(2e5 draws, pure drift, k>=0) found no case where the unclipped null sum <= k while the clipped one > k, so the claim appears
true, but the proof does not show it (and the jump class is untested). Fix: let the null follow the max-rate drop clipped at -1,
which is in C; then T1 holds with S_clip(d,h) = (1/h) sum_j min(drop(d+j), L+1); state T1 with S_clip (equal to S whenever
L - drop(d+h-1) >= -1). Also fix notation: P_tau is defined as sum mu - k, so the null event is P_tau <= 0, not "<= k".
Also T1 is proved for the constant-history world only; "in every world whose history is a prefix of a null path" is correct and
general. Oblivious vs adaptive adversary: irrelevant for a lower bound (oblivious nulls are a subset).

### T2 statistical lower bound: GAP (fixable); core proof VERIFIED
Checked: P- is in C (steps exactly v, then v); its horizon average equals k/h by construction; chain rule for adaptive
experiments with common query kernel; KL_i monotone in age so B requests contribute at most sum_{m<B}; data processing with
kl(1-beta||alpha) monotone (needs 1-beta>alpha, unstated). The inequality (*) is sound.
Gaps:
1. Asymptotics assume unit variance: for Rademacher, KL(Rad(L)||Rad(L-delta)) ~ delta^2/(2(1-L^2)), so sqrt(2 kappa/B) and
   (6 v kappa)^{1/3} hold only as L->0; the ledger's "~" statements need the (1-L^2) factor (fix: write gamma_lb ~ sqrt(2 kappa
   (1-L^2)/B)). The numerical gamma_lb uses exact KL so the code is right, the prose is not.
2. Lower bound is for validity at fixed (tau,h) only (the proof never uses adaptive tau) and for a certifier that knows tau in
   advance (requests can be placed in the last B rounds before tau-d). The UB (B2 window) likewise assumes known tau. So the
   frontier is for the "known-decision-time" problem; a real switch is not announced, and this is not a lower bound for the
   operational problem (B1/B2 pilot delays of 38-120 rounds are outside the theory).
3. "Tight within 2.4x" is computed on a narrow grid: alpha=.05, beta=.2, base=.1, v in {0,.002,.01}, B in {50,200,1000}
   (frontier.json also lists B=6,10,14, where gamma_ub = 1.73, 1.34, 1.13, i.e. L = gamma+base > 1 is infeasible; the exact
   Neyman-Pearson sandwich was only run in these B<=14 cells where the UB is vacuous). On my wider grid (alpha 1e-3..0.2,
   beta 1e-3..0.5, v 0..1e-2, B 50..1e4, base 0/.1/.3; 950 feasible cells) the UB/LB ratio is 1.50 to 4.71 (median 2.09);
   the worst cases are large alpha with beta=.5 and base=.3 (4.7), and beta<=.01 gives up to 3.28 because kl(1-beta||alpha)
   saturates at ln(1/alpha) while the UB grows with ln(1/beta) (Bretagnolle-Huber/exact NP would be needed). At the headline
   (alpha,beta)=(.05,.2) the max ratio over my grid is 2.36, so "2.4x" is correct only there.
4. LB uses exact Bernoulli KL while the UB uses range-only Hoeffding: part of the ratio at larger L is the variance mismatch
   (T8), not intrinsic looseness; and "exact (additively) in d,h,k" holds only because d,h,k enter solely through base, by
   construction of both bounds; it carries no information.
5. LB covers the pure-drift class only; the jump/dwell class used in T5 and the pilot has no LB (T7).
6. "Budget saturates at B_sat=(c/v)^{2/3}" is the UB's optimum; the LB saturates at gamma/v; the claim "nothing beyond helps" is
   only true up to constants.
Score: lower bound is a correct Le Cam/KL argument (not new).

### T3 achievability (B2): (a) validity VERIFIED under stated assumptions with SCOPE GAP; (b) rate GAP (fixable)
(a) Checked line by line: increments Z - mu_{s_i} are 1-sub-Gaussian (range 2, Hoeffding lemma) conditionally on the full
filtration G (including unreleased labels), so S is a G-martingale in request order even though the certifier sees only the
released sub-filtration (the query decision is G-predictable); mixture supermartingale algebra is right (Gaussian integral gives
sqrt(rho/(m+rho)) exp(S^2/(2(m+rho)))); Ville gives P(sup M >= 1/alpha_b)<=alpha_b; inversion gives u(m) exactly as in
`mixture_boundary`; union alpha_b = alpha/(b(b+1)) sums to alpha; the deterministic implication
sum mu_{tau+j} >= h(Zbar - u/m) - (1/m) sum drop holds pathwise on the good event for all (tau,h,batch), so adaptive tau/h and
adaptive (predictable-mean) adversaries are covered. Two-sided boundary used for a one-sided test is conservative (alpha_b
effectively doubled), consistent with the observed <=.0169 at alpha=.05.
Scope gaps (all fixable by stating them): (i) delay must be non-adaptive (constant d, or independent of labels); the proof uses
that the released set is a prefix in request order. With label-dependent release order or selective release (out-of-order,
selectively sampled feedback, which the repo guide requires to be explicit) the released subset is not a stopped prefix and
validity fails (adversary releasing high labels first certifies a null w.p. near 1). (ii) rho = rho(n_b) and n_b are F_{r_b}
measurable: fine. (iii) the guarantee is relative to the declared class C; misspecification gives no guarantee (as T5 shows).
(iv) every batch spends alpha/(b(b+1)); the b-th certification attempt pays an extra 2 ln(b(b+1)) in the radius, so "valid at any
batch" is bought with a price that grows with the number of attempts; the frontier numbers are for b=1 only.
(b) Rate: algebra checks (gamma >= [u(n) + sqrt(2 ln(1/beta) n)]/n + v(n-1)/2). Gap: the UB constant is the single-batch Hoeffding
value; the B2 ratio 2.0-2.65 was obtained at alpha=.05, beta=.2 with batch 1 (alpha_b=alpha/2) and the window of n latest labels
requires a batch committed so that its last request is exactly tau-d (known tau; see T2 item 2). Numerical MC of validity is
oblivious-adversary only (N=150 per tight null), so adaptive-adversary validity rests on the proof, not the simulation.

### T4 optional-continuation counterexample: VERIFIED (exact), WEAK as stated
My independent DP (integer random walk, mean .1, rule Zbar - sqrt(2 ln(1/alpha)/m) > .1) gives .00837 (M=10), .05012 (M=100),
.07054 (M=300), .09287 (M=1000): matches the ledger. The M=100 violation is marginal (.0501 vs .05); a single pre-committed look at
m=100 has error .0055 (Hoeffding is ~9x conservative at one look), so the "naive Hoeffding is invalid" demonstration only bites at
M>=100 and is a mild 1.9-2.4x at M=1000-5000; the Gaussian-naive version (5.6x at M=100) is the persuasive one. Not new (peeking).

### T5 persistence alone insufficient: VERIFIED (trivial) / pilot part DESCRIPTIVE
Formal part: S>=J (since ceil(a/hd)>=1 for a>=1) and J>=2L gives L - k/h > S impossible for L>0; correct (needs J<=1+L for the
completion to stay in [-1,1], else apply clipped T1). It is a corollary of T1, not an independent result. The pilot (flip case)
violates the declared v by construction, so "drift-class certificates certify wrongly" is class misspecification, expected, and
"B2 refuses with honest class" is T1 operating. Dev pilot, N=300, not confirmatory.

### T6 price of time-uniformity: UNVERIFIED (conjecture)
Even if true it is second order: sqrt(ln ln n / n) vs the bias-dominated optimum n*~v^{-2/3}; for K attempts the ln K lower bound
fails when attempts reuse the same data (correlated tests). The required statement (finite-B, drift class, lower bound vs
union-free stopping) is not derived. Classical LIL lower bounds exist (not retrieved).

### T7 jump-class lower bound: UNVERIFIED (conjecture)
Plausible via best placement of one jump, but the interaction of jump placement with the unobserved tail S (which already
contains J) is not worked out; without it, the headline class (J,hd) has an upper bound only.

### T8 variance-adaptive frontier: UNVERIFIED (conjecture, not implemented)
Note: the LB already uses exact Bernoulli KL, so the LB/UB gap at large L (the regime needed for non-vacuity, L~.45) is inflated by
the range-based UB; a Bernstein/betting CS (Waudby-Smith-Ramdas, Chugg-Ramdas, not read) is the obvious fix and is known technique.

## Prior-art reduction (provisional)
T0 = TV identity; T1 = bounded-drift nonidentifiability (repo doc + elementary); T2 = two-point Le Cam / KL with a
variation-budget bias term (Besbes-Gur-Zeevi style, not read in full); T3 = normal-mixture CS (Howard et al., abstract only)
plus age-bias window; the Chugg-Ramdas snippet suggests CS for drifting conditional means exist, so the drift-bias CS is likely
covered. Nothing here constitutes a new technique; novelty is the combination for payback-with-delay-and-request-budget.

## Strongest kill argument (headline B), ~200 words
The "frontier" is a Le Cam two-point bound matched by a Hoeffding window plus a mixture confidence sequence, with the drift
slack added by hand; every ingredient is textbook (variation-budget tracking, normal-mixture CS, binary-KL data processing). The
"matching up to 2.4x" claim is computed at one (alpha,beta)=(.05,.2), base=.1 point; on a wider grid the gap reaches 3.3 to 4.7,
the exact-NP sandwich lives only in B<=14 cells where the upper bound needs L>1 and is vacuous, and "exact in d,h,k" is true by
construction. Both bounds assume the decision time tau is known in advance and constant, label-independent delay; neither
applies to the operational problem, where the pilot shows 38-120 rounds of lateness. Non-vacuity needs L~.45 with +/-1 labels,
and the variance-adaptive fix (T8) is unproven. The persistence result T5 is T1 with J>=2L, and the flip stress merely violates
the declared class. T6, T7 and T8, which would carry the novelty (jump class, time-uniform price), are conjectures. The lone
non-trivial new object, the optional-continuation counterexample, is a 1.9-2.4x inflation of a Hoeffding test, i.e. peeking.
B is a correct short proposition, not a headline.

## Best defence, ~150 words
Every stated step of T0-T4 survives line-by-line checking, and the code matches the proofs (13 tests pass, my independent DP
reproduces T4, the clipping worry produced no numerical violation). The contribution is a formal certification problem that none
of the repo's detectors addresses: payback of a switch under label delay, request-time-booked budget and bounded drift, with
(i) an exact impossibility (T0/T1) separating what no sample size can buy from what budget buys, (ii) a time-uniform certificate
valid under adaptive stopping, adaptive (tau,h) and predictable adversaries, and (iii) a frontier whose dependence on
(B,v,alpha,beta) matches within a constant at the headline setting and exactly in the additive slack. The dev pilot shows
conventional certificates (B0 family, B1n) violate alpha on in-class nulls while B2 does not, and that honest persistence
declarations make certificates refuse, which operationalises "alarm is not harm". Positioned as a short result plus
counterexample, it is a defensible supporting section.

## Summary table
| Thm | Verdict |
|---|---|
| T0 | VERIFIED (trivial) |
| T1 | GAP (fixable: clipped slack S_clip, P_tau notation) |
| T2 | GAP (fixable: variance factor, known-tau scope, tightness grid; core proof verified) |
| T3a | VERIFIED with scope GAP (non-adaptive delay, b-dependent price) |
| T3b | GAP (fixable: single-batch, known tau, alpha/2) |
| T4 | VERIFIED (exact), weak |
| T5 | VERIFIED (trivial corollary of T1) |
| T6, T7, T8 | UNVERIFIED (conjectures) |
