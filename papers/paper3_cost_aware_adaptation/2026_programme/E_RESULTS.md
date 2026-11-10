# E results: kill test for dual-use labels (2026-11-09)

Verdict: STOP. Prequential certification of a retrained challenger is valid for the per-round predictable-version null (no cost from label
reuse). The "promoted frozen version" gap appears only under non-stationarity and is reproduced by label-reuse-free holdout certification, so it
belongs to candidate B, not E. HE-1 is falsified in its label-reuse form; HE-2 is falsified (no split beats always-train at valid level). E
collapses into Challenger + prequential e-process (ALREADY_COVERED by predictable-monitoring prior art).

All numbers are in ledger/dualuse.jsonl. Dev seeds: base 9,100,000 (kill, R=40,000, Wilson 95%), 9,150,000 (J pilot, R=4,000); smoke 9,000,000.
alpha=.05, T=600, d=5, 0-1 loss, SGD logistic, m=5 (noise_m40: m=40). One learner config; no tuning.

## K1 boundary null (labels pure noise: every version has E[Z|F]=0 exactly)
| gate | rate | 95% CI |
|---|---|---|
| prequential, accumulated across versions, m=5 | 0.0306 | [.0289,.0323] |
| prequential, m=40 | 0.0317 | [.0300,.0335] |
| 50/50 split (train odd, certify even) | 0.0251 | [.0236,.0267] |
| frozen holdout (train 40 rounds, then certify) | 0.0288 | [.0272,.0304] |
| resubstitution (version updated with label t, then tested; not predictable) | 1.000 | [.9999,1] |
| naive sequential z peeking | 0.295 | [.290,.299] |
| per-version restart e-process, no spending, m=40 | 0.0686 | [.0662,.0711] (exceeds alpha) |
| same with alpha/((v+1)(v+2)) spending, m=40 | 0.0012 | [.0009,.0016] |

Stationary Bayes-optimal incumbent (strict null): prequential 2.5e-5 (1/40000); all valid gates below 1e-3; promoted frozen forward value is
nonpositive in 100% of promotions.

## K2 non-stationary forward null (periodic flip, half-period L=100, random phase, f0 fixed, w0_cos .3)
Any frozen classifier pair has exactly zero expected excess over a 2L window (risk_+ + risk_- = 1 pointwise), so N_fwd(200) holds with equality
for every version, yet:
- the prequential gate promotes in 0.8946 [.8916,.8976] of runs. P(promoted and forward value <= 0): h=200 0.8946; h=100 0.8085 [.8046,.8124];
  h=50 0.5237. Mean forward value of the promoted frozen version at h=100 is -15.5 loss units vs incumbent.
- Control without label reuse: frozen holdout candidate promoted in 0.2483 [.2441,.2526]; split gate 0.2450.
N_round is false here (the tracking learner beats f0 per round), so no validity statement is violated; the object worth deploying is the running
adaptive learner, not a frozen snapshot.

## J pilot (stationary, T=600, B=240 labels, delay 10, c_q=.05, c_r=.05, k=3, R=4000; dJ = J(policy) - J(prequential-all), paired 95% CI)
| world | split25 | split50 | split75 | never switch |
|---|---|---|---|---|
| alt cos .3 (strong benefit) | +33.0 [32.2,33.9] | +32.8 [32.0,33.7] | +45.5 [44.6,46.4] | +39.1 |
| alt cos .7 (mild) | +0.9 [0.6,1.1] | +1.2 [0.9,1.4] | +2.3 [2.0,2.5] | -11.1 [-11.3,-10.8] |
| alt cos .3, delay 40 | +22.6 | +22.5 | +29.7 | +20.4 |

Positive dJ means the split is worse. Valid dual-use dominates every split; in the mild world never-switch beats all valid gates (no net benefit
after k and fees). Invalid fast rules win J but break the constraint: IN_HOUSE discounted Wald-LCB with label cutoff (adapted from
origin/research/paper1-eqsdp-foundation-2026-11-08@5bda4e73:scripts/paper1_eqsdp/stage2_policies.py Stage2Wald; not a native port) has
false-promotion 0.304 on noise labels and J gap -22.8 in alt cos .3; IN_HOUSE plug-in adopt-after-n ("Challenger-style", not the paper's rule)
0.863 and -32.2.

## Limitations
Synthetic only; no real stream run (kill outcome did not warrant it). No rollback. K2 forward truth is evaluator-side. Wald and Challenger
baselines are in-house heuristics. Effect grades: K2 gap large but drift-driven; split-vs-dual J gap substantial in strong-benefit worlds,
small (~0.5%) in mild ones.
