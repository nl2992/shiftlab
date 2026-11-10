# 03B Payback certification (workstream B): design, results, verdict

Status: theory + dev pilot. Code `src/shiftlab/paper3/payback/`, tests `tests/paper3/payback/` (13 pass),
scripts `scripts/paper3/payback/`, outputs `outputs/paper3/payback/`, ledger `ledger/payback.jsonl`.
Theorem statuses and proofs: `06_THEOREM_LEDGER.md`.  No confirmatory run has been made.

## Registered dev seeds
`SeedSequence([5301500000, class_idx, i])`, i < 300 (sub-range 5301500000-5301599999 of the dev block in
`configs/paper3/seed_registry_v1.json`); smoke base 5300500000. Pilot tag `pilot1` (N=300/class).
Setting: T=400 (500 for flip), B=150, d=5, hold h=30 (100 for flip), k=3, alpha=.1, declared v=.002, labels +/-1
(Rademacher, inside [-1,1]); single switch, hold-for-h; all certifiers see the same query schedule
(batches of n_plan=plan_batch_size labels, budget reserved at commitment, request-time booking, delay d).

## Certificates
B0a window-Hoeffding LCB + hurdle (IN_HOUSE); B0w Gaussian-window LCB (IN_HOUSE); B0b Regol-style OLS-trend
forecast quantile (IN_HOUSE adapter; Regol et al. not retrieved); B1 age-corrected Hoeffding envelope of
`docs/switching_mechanism_screen_v1.md`, evaluated only on completed batches; B1n = B1 with optional continuation
(invalid); B2 per-batch normal-mixture confidence sequence (sub-Gaussian 1), alpha_b = alpha/(b(b+1)), valid at any
arrival, any (t,h), any batch; envelope class C(v,J,hd) generalises drift to drift + jumps of size <= J separated by
>= hd (the persistence / dwell parameter).

## Exact results
* Reversal impossibility, exact (Fractions, all adaptive-query histories, all 2^|H| rules): two worlds sharing the
  history law give min(type I + type II) = 1 exactly; if one visible label differs the sum is < 1.
* Optional-continuation counterexample (exact DP, world on the null boundary mean = k/h = 0.1, alpha = .05; float
  DP agrees with rational DP to 1e-12 at M=40). P(some look certifies):

| looks M | Hoeffding-naive | Gaussian-naive (z=1.645) | B2 mixture CS |
|---|---|---|---|
| 10 | .0084 | .119 | 0 |
| 30 | .0279 | .200 | .0010 |
| 100 | **.0501** (> alpha) | **.280** (5.6 alpha) | .0058 |
| 1000 | .0929 (1.9 alpha) | .407 | .0140 |
| 5000 | .1221 (2.4 alpha) | .482 | .0169 |

A single pre-committed look at n=100 is valid (< alpha); continuing/choosing n after seeing data is not.
B2 stays <= alpha for all alpha in {.2,.05,.01}, mu0 in {0,.1,.5}, m* in {20,200}, M=1500 (test).

## Frontier (alpha=.05, beta=.2, base = k/h + slack = .1; `frontier.json`)
gamma_lb (KL bound) <= gamma_NP (exact Neyman-Pearson on the constructed pair, B<=14) <= gamma_ub (Hoeffding window).
UB/LB: 2.4 (B=6,v=0) falling to 1.8-2.2 for large B; v^{1/3} regime: LB = 2.24 v^{1/3}, UB = 3.93 v^{1/3}
(ratio 1.75, v=1e-5..1e-3). B2 (mixture, power by Hoeffding): ratio 2.0-2.65. Budget saturates: at v=.002 nothing
beyond B ~ 165 changes either bound. Non-vacuity needs L > k/h + v(d+(h-1)/2) + gamma: with +/-1 labels and
v=.002,B=150,h=30 that means L ~ .45 or more, a large effect; variance-adaptive (Bernstein/betting) bounds are
needed for realistic Delta (not implemented here).

## Dev pilot (pilot1, N=300/class; P(wrong) = P(certified with true hold payback <= 0))
Columns: cert rate / P(wrong) / mean delay of certified / mean labels / mean realised net per stream (uncert = 0).

| class | B0a | B0w | B0b | B1 | B1n | B2 |
|---|---|---|---|---|---|---|
| drift (in) | .99/0/26/26/16.4 | 1.0/0/11/10/16.3 | 1.0/0/17/16/16.2 | .81/0/121/126/14.5 | .91/0/36/46/15.5 | .78/0/48/69/14.2 |
| boundary (in) | .99/0/22/23/16.7 | 1.0/0/10/10/16.8 | 1.0/0/15/14/16.5 | .75/0/120/127/10.0 | .86/0/27/43/15.0 | .75/0/38/66/13.5 |
| dwell J=.15,hd=40 (in) | .99/0/23/23/16.3 | .99/0/10/10/16.4 | 1.0/0/14/14/16.5 | .45/0/65/111/10.3 | .51/0/41/94/11.0 | .29/0/55/122/7.1 |
| null_flat (in-class null; every cert wrong) | .13/**.127**/58/138/-.16 | .54/**.537**/26/83/.47 | .81/**.810**/28/51/-.01 | 0/0 | .01/.010 | 0/0 |
| null_decline:60 (tight null, wrong after t=60) | .26/.053/39/121/.52 | .83/.060/21/43/1.78 | .81/.050/23/46/2.13 | 0/0 | .05/.007 | 0/0 |
| STRESS reversal .9 | .91/.120/23/33/11.4 | .98/.040/11/13/13.9 | .98/.060/15/16/13.5 | .28/.280/119/141/-1.7 | .74/.113/26/57/9.3 | .57/.083/35/84/8.0 |
| STRESS drift 3v | .93/.017 | .99/.003 | .98/.003 | .53/.087 | .77/.007 | .65/0 |
| STRESS dependent labels | .98/0 | .99/0 | 1.0/0 | .74/.003 | .92/0 | .83/0 |
| STRESS flip hp=100 (E case) | .82/.603/55/72/-18.6 | .88/.590/46/58/-12.3 | .99/.433/28/27/4.2 | .25/.203/148/149/-9.8 | .66/.490/69/96/-17.1 | .44/.350/76/117/-13.7 |
| flip, B2 with honest envelope (J=1.8,hd=100) | | | | | | **0 / 0 / refuses** |

Reading (descriptive, dev only; not confirmatory):
* Validity on in-class nulls (alpha=.1): on the flat null (payback exactly 0) the B0 certificates exceed alpha:
  B0a .127, B0w .537, B0b .810 wrong-sign certification; B1, B1n (.010) and B2 (0) do not. On the tight decline
  null all are below alpha (B0 .05-.06), so B0's failure there is not shown. (A first pilot run mis-scored
  null_flat because of float rounding in the payback test; fixed with a 1e-9 tolerance and rerun.)
* Price of validity: B2 certifies later (38-48 vs 10-26 rounds) and spends 2-3x the labels; realised net is
  ~2 units (13%) below B0 in the easy in-class classes. Where the class is violated, that ordering reverses.
* Flip case (coordinator's E stress): drift-class certificates (B0, B1, B2) certify wrongly in 20-60% of runs
  (P(wrong | certified) ~ .7-.8; realised net -10 to -18). Declaring the true persistence (J=1.8, hd=100)
  makes B2 refuse (0 certifications, net 0): this is Theorem 1 operating, not a power result. Validity holds only
  under the declared class; an e-process gate's historical validity gives no protection (E_RESULTS: 89% promotion,
  P(promoted and forward value <= 0) = .81).
* B1 as a post-hoc certifier is hurt by its fixed late completion time (stale evidence).

## Verdict (honest)
See `06_THEOREM_LEDGER.md`. B carries a clean, fully proved, numerically checked finite-sample frontier and a
valid time-uniform certificate, but every ingredient is known or elementary (variation-budget tracking bounds,
Le Cam / data processing, confidence sequences, delay as an additive age shift). Recommended status: ALREADY_COVERED
as a headline; usable as a supporting proposition + the optional-continuation counterexample.
