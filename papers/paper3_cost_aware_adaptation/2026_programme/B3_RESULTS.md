# B3 results: variance-adaptive payback certificate (DEVELOPMENT; nothing here is confirmatory)

Design and pre-run protocol: `03B3_VARIANCE_ADAPTIVE_DESIGN.md` (written before any real run). Validity argument:
PROOF_SKETCH (not audited). Code `src/shiftlab/paper3/payback/variance_adaptive.py`; tests
`tests/paper3/payback/test_variance_adaptive.py` (5) + existing payback tests: 22 pass. Outputs
`outputs/paper3/payback/b3/`; ledger records kind `B3_*` in `ledger/payback.jsonl` (git cee36098+dirty).
Commands (PYTHONPATH=src, OPENBLAS_NUM_THREADS=1): `b3_synth.py 1000`, `b3_optcont.py 2000`,
`b3_real.py --split even --certs B2,C0,C1,C2,C3,C4`, `b3_real.py --split odd --certs B2,C3 --v {.002,.001,.0005} --h {100,50}`,
`b3_analyze.py`, `b3_vs_wald.py`.

## Headline
1. B3 (PrPl-EB, single CS) is valid in every synthetic test and weakly more powerful/faster than B2 where B2 has power.
2. On c4 at the declared class (v=.002, d=100) **B3 is still vacuous**: 3 certifications in 1,080 odd episodes (B2: 1).
   The binding constraint is the irreducible slack of T1 (hurdle .329 at h=100 versus stream mean Z of -.04 to .24), not the
   range-based radius. Variance adaptivity cannot fix this; it is an identifiability limit of the declared class.
3. B3 does not close the gap to the invalid repeated-look B0a/B0w (still significantly negative). Versus B0b it is not
   distinguishable.

## 1. Synthetic validity (N=1000 per class, T=400, B=150, d=5, h=30, k=3, alpha=.1, v=.002; seeds [5301600000, class, i])
P(wrong) = P(certified with true hold payback <= 0); Wilson 95% upper bound shown. alpha=.1 requirement met by every cell.

| class (null) | B2 | B3 batch s=1 | B3 batch s=.25 | B3 single s=.25 | B3 gated (M2) |
|---|---|---|---|---|---|
| null_flat | 0 (<.004) | 0 | 0 | .007 (<.014) | n/a |
| null_decline:60 | 0 | 0 | 0 | .001 (<.006) | n/a |
| sparse flat p=.15 | 0 | 0 | 0 | 0 | 0 |
| sparse flat p=.30 | 0 | 0 | 0 | 0 | 0 |
| sparse decline p=.15 | 0 | 0 | 0 | 0 | 0 |
| sparse decline p=.30 | 0 | 0 | 0 | 0 (cert .002) | 0 (cert .001) |

Caveat: these tight nulls carry slack, so all certifiers (B2 too) certify almost never; this table alone is a weak
stress. The sharper test is the zero-slack optional-continuation world below.

Optional-continuation world (mu = k/h = .1, no drift term, no delay, one sequence, looks m <= M; MC N=2000):
P(some look certifies), B3 vs Gaussian-naive (sample-sd z-test at each look):

| alpha | bets | M=10 | M=100 | M=1000 | Gaussian-naive M=1000 |
|---|---|---|---|---|---|
| .05 | lam_max .5, Rademacher | 0 | .0095 | .0125 | .56 |
| .10 | lam_max .5, Rademacher | 0 | .029 | **.0395** | .67 |
| .10 | lam_max .5, sparse p=.3 | 0 | .0085 | .0245 | .58 |
| .10 | lam_max .75, Rademacher | .007 | .0185 | .0205 | .67 |

All <= alpha (max .0395; MC standard error <= .005). (The existing 03B table uses a different naive rule: Hoeffding-naive and
z=1.645 with known variance.)

In-class power and delay (same setting; cert rate / mean delay of certified / mean labels / realised net per stream):

| class | B2 | B3 batch s=1 | B3 single s=.25 | B3 gated |
|---|---|---|---|---|
| drift (+/-1) | .773 / 43.8 / 67 / 14.15 | .787 / 35.6 / 59 / 14.37 | .828 / 29.9 / 50 / 14.68 | n/a |
| boundary (+/-1) | .735 / 41.5 / 70 / 12.92 | .766 / 35.0 / 61 / 13.39 | .817 / 29.5 / 51 / 14.08 | n/a |
| sparse in-class p=.30 | 0 | .003 | .007 / 59.9 / 149 | .004 / 38.8 / **19** |
| sparse in-class p=.45 | .003 | .151 / 66 / 137 / 1.29 | **.257 / 58.7 / 126 / 2.06** | .183 / 49.0 / **28** / 1.43 |

Reading: variance adaptivity gives B3 a modest gain over B2 for +/-1 labels (variance there is already ~1; the gain is mostly
the single-CS alpha saving: ~+5 points cert rate, ~14 rounds earlier). On sparse Z the gain is large only where the effect clears
the hurdle (p=.45), from ~0 to .26. Gating (M2) gives the same evidence as ungated B3 on the same window (all rounds are
known either way) but spends **~28 instead of ~137 labels** (it saves the label bill, not power); the window cap from the
batch plan, not the budget, binds, so M2 does not stretch the budget to B/p_dis rounds here.

## 2. Real c4 development (EVEN episodes, 27 streams, 1,089 episodes, v=.002, h=100, c_q=0)
Tuning budget: 5 configurations; mean net per episode (stream-equal): B2 .061; C0 .093; C1 .066; C2 .065; **C3 .1185**; C4 .094.
Certifications of 1,089: B2 1, C0 2, C1 1, C2 1, C3 3, C4 2 (kc_311, sf_311 only). Rule picks C3 (single CS, sigma_plan=1,
lam_max=.5). The differences between configurations rest on 1-3 episodes and are noise; selection was mechanical.
M2 not used on c4: true disagreement is observable in the contract but not stored in the npz (design section 2).

## 3. Real c4 evaluation (ODD episodes, evaluated once; 27 streams, 1,080 episodes; stream-cluster bootstrap 10,000, seed 20261110)
Primary: h=100, c_q=0, v=.002. B0a/B0w/B0b/B2 are the R1 odd-episode rows (my driver reproduces R1's B2 exactly: confirmed).

| cert | cert rate (stream mean) | n cert | wrong-sign (pooled) | delay t | labels | net c_q=0 | net c_q=.05 |
|---|---|---|---|---|---|---|---|
| B3 | .003 | 3 | 1/3 | 138 | 150.0 | 0.079 | -7.42 |
| B2 | .0007 | 1 | 1/1 | 129 | 150.0 | -0.004 | -7.50 |
| B0a | .084 | 94 | .043 | 163 | 149 | 1.93 | -5.53 |
| B0w | .365 | 382 | .322 | 133 | 140 | 3.01 | -3.98 |
| B0b | .836 | 901 | .615 | 136 | 128 | 1.33 | -5.09 |

Contrasts (mean per episode, [95% CI]); h=100:
| contrast | c_q=0 | c_q=.05 |
|---|---|---|
| B3 - B0a | -1.85 [-3.73, -0.40] | -1.89 [-3.74, -0.43] |
| B3 - B0w | -2.94 [-5.44, -0.89] | -3.44 [-6.05, -1.26] |
| B3 - B0b | -1.25 [-3.97, +1.02] | -2.33 [-5.14, +0.04] |
| B3 - B2 | +0.08 [0.00, +0.21] | +0.08 [0.00, +0.21] |

h=50, c_q=0 (secondary): B3-B0a -0.71 [-1.44,-0.15]; B3-B0w -0.97 [-2.01,-0.15]; B3-B0b +0.50 [-0.80,+1.58]; B3-B2 +0.06 [-0.00,+0.13];
B3: 5 certifications (1 wrong-sign).
The B3-B2 gain is +0.08 per episode driven by 2 extra certifications; its CI lower bound is 0.0 (not a result).
Wrong-sign here is the realised hold sum <= k, not a violation of the mean-based guarantee.

### Pre-registered sensitivity: declared v (NOT the declared class; validity only if the declaration is true)
h=100, c_q=0, odd episodes, B3 vs B2 under the same declared v:
| declared v | hurdle k/h+S | B3 cert / wrong-sign / net | B2 cert / wrong-sign / net | B3-B2 | B3-B0a | B3-B0w | B3-B0b |
|---|---|---|---|---|---|---|---|
| .002 | .329 | 3 / 1 / .08 | 1 / 1 / -.00 | +.08 [0,.21] | -1.85 [-3.73,-.40] | -2.94 [-5.44,-.89] | -1.25 [-3.97,+1.02] |
| .001 | .180 | 24 / 1 / .64 | 11 / 1 / .28 | +.37 [.10,.70] | -1.29 [-2.68,-.26] | -2.37 [-4.47,-.69] | -.69 [-3.04,+1.30] |
| .0005 | .105 | 61 / 1 / 1.45 | 21 / 2 / .51 | +.94 [.19,2.02] | -.48 [-.98,-.10] | -1.57 [-2.85,-.49] | +.12 [-1.45,+1.65] |
Even at v=.0005 (a quarter of the declared drift; descriptive 100-lag drift of the real streams is .0008-.0036 per round, so
that declaration is probably FALSE for many streams) B3 certifies 5.4% of episodes with 1.6% wrong-sign, beats B2 clearly, ties B0b and
B0a is still above it (CI excludes 0), B0w is far above. This quantifies that the vacuity is the declared slack.

## 4. Secondary: B3 as a switching rule vs Paper 1 Wald+cutoff (odd episodes, transfer-port contract)
J = loss + c_q*labels + c_s*switches, T=2000, c_q=.05, c_s=5 (`transfer/sim.py` PRIMARY; B3 holds the challenger to episode end
after certification). Stream-equal mean J: never-switch 496.2; **B3 502.2**; Wald+cutoff(.98,.3,H=300) 426.0; Paper 1 ref (.97,.2) 427.1.
B3 - Wald+cutoff = +76.1 [35.9, 124.8] (B3 worse); B3 - never = +6.0 [3.6, 7.5] (B3 ~= label bill 7.5, no switching).
Contract differences: B=150 vs 200, B3 buys a label every round of its batch (not disagreement-gated, because the
disagreement indicator is not stored for c4), one switch only, payback certificate targets h=100 not the remaining horizon,
Wald is multi-switch with paced purchases. This is a contract-mismatched comparison; it says only that a
payback certificate with the declared slack is not an economic switching rule.

## 5. Honest assessment
* B3 achieves the stated validity goal and is better than B2 (valid and non-vacuous in sparse/small-variance synthetic
  worlds that B2 cannot handle at all, e.g. p=.45: .003 -> .26), but the real-effect-size goal is not met on c4 at the declared
  class: irreducible slack (T1) exceeds every stream's mean advantage except in a few sf_311/dc_311/kc_311 episodes.
  The "non-vacuity needs mean ~.45" statement in 03B was mostly slack, not radius: with exact knowledge of the label mean the
  hurdle is still .329.
* A practical certificate needs either a smaller declared drift (justified independently of payback, which the real streams
  do not support at .0005) or shorter label delay, or a different estimand than "payback over the first 100 rounds after a switch
  that must be decided d rounds after the last label".
* M2 (disagreement gating): sound and ~5x cheaper in labels on synthetic data; unusable on c4 as stored (needs predictions).
* Verdict for Paper 3: B3 improves the valid-certificate branch but does not reverse R1's finding that, on real streams, the
  invalid hurdles out-earn any valid certificate in this class. Continue only as a supporting section (certificate + T1
  slack explanation); not a headline. Not confirmatory; all c4 data exposed.
* Limitations: single dev setting for synthetic (d=5, T=400); no hold-horizon grid in synthetic nulls; oblivious null paths
  only (adaptive adversary rests on the proof sketch); the PrPl-EB lemma (Fan-Grama-Liu 2015) and WSR Thm 2 were cited from
  the repo port and memory, not re-retrieved; dwell class not tested for B3.
