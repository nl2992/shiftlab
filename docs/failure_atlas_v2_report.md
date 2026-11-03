# Failure Atlas v2: report

2026-11-03, branch `claude/failure-atlas-v2-sota-195428` (merges
`research/atlas-local-checkpoint-2026-11-01` and `research/b3-generalisation-icml`; no earlier
result changed). Commits: `ade273f` protocol and harness, `1ee1060` development freeze,
`5167995` validation. Detailed documents: [protocol](failure_atlas_v2_protocol.md),
[atlas](failure_atlas_v2_atlas.md), [development](failure_atlas_v2_development.md),
[validation](failure_atlas_v2_validation.md).

**Bottom line.** A shared failure was found and an attachable repair confirmed on the
registered synthetic family. That result is a narrow, competitive-but-incremental improvement,
not yet a publishable SOTA algorithm: the margin over the strongest error-controlled
comparator is 2.8-3.7 cost units (~1%), it comes from late-change regimes, it does not hold on
strong stationary improvement against front-loaded Gated, it fails under Markov dependence, and
no real-data advantage was observed. Verdict: **continue, scoped**, with one decisive next test.

## 1. Unified Failure Atlas v2

15 policies (10 published-method adapters incl. three ported on 2026-11-03 from the mandatory
registry, P7s, two controls) x 20 synthetic regimes x 100 seeds + 9 real replay streams; 80,400
runs. Matrix, promotion rates, expected-oracle regret, label use and promotion delay:
[failure_atlas_v2_atlas.md](failure_atlas_v2_atlas.md),
[discovery_tables.md](failure_atlas_v2_results/discovery_tables.md).

Registry coverage: run as adapters — Gated/off-policy CS (1), DISCERN-style (2), Gong & Zhang
Alg. 1 (4, ported), CAMS constant-policy (5), Model Selector causal (6), Model Picker (7),
variance-min + IPW (8), SMCS + retain rule (9), Online LLM Picker (10), Qiu et al. Alg. 1-3
(11, ported), Ryabchenko et al. delayed FTRL (13, ported). Not run: Sawade calibrated (3; needs
features), The Challenger (12; retraining learning-curve setting, no frozen-model rule). Native
verification against author code exists for CAMS, Model Picker, variance-min, SMCS, Model
Selector (earlier programme); none for the three new ports.

## 2. Selected failure mechanism

**M1, over-conservative certification**, shared by four independently developed
error-controlled families (Gated/MOPE CS, DISCERN/EB-CS, Xu/active-testing betting + P7s,
SMCS e-values; also our Qiu port): a clearly better challenger is rarely promoted within the
horizon (Gated promotes in 7% of F0_better runs, DISCERN 0%). Mean cost gap to the best method:
+65.6 on stationary synthetic alternatives, +102 on the five real streams with a better
challenger. Opposite failure M2: the seven online selectors promote on null/worse challengers
82-100% of the time.

Causal decomposition (development ablations, Gated): (a) inverse-propensity range under paced
acquisition — front-loading alone 432.5 -> 394.3 on stationary alternatives; (b) cumulative,
stop-at-verdict evidence — late-change cost stays at 402 with front-loading and falls to 379
only with a restart mixture.

## 3. Working algorithm

`scripts/failure_atlas_v2/restart_monitor.py`.

* **RMM (attachable).** Label-clock outcomes X_n = +-D on queried disagreements (no inverse
  weights); detector M_n = mean over lambda in {.15,.3,.5} of sum over restart starts s (every 10
  labels, prior mass 1/|S|) of prod_{k>=s}(1 + lambda X_k); alarm at 1/alpha_det; continued
  paced acquisition after the base's verdict; on alarm switch, restart the base, reset the
  detector. Base at alpha/2, detector at alpha/2. Valid (Ville) for the first promotion under
  the uniform conditional null; audit confirmed the supermartingale bookkeeping.
* **LRMD (standalone).** Same detector, all alpha, w_first=.5 start prior, acquisition
  q_t = min(1, 2 remaining / (rate (T - t))).

## 4. Competitive benchmark (frozen validation, 13 new regimes, seeds 5000-5099)

Primary family (late improvement + stationary better), per-seed family mean:

| contrast | mean [95% CI] |
|---|---|
| Gated+RMM - Gated | -25.61 [-27.16, -24.09] |
| DISCERN+RMM - DISCERN | -27.06 [-28.53, -25.59] |
| SMCS+RMM - SMCS | -8.21 [-9.79, -6.59] |
| Gated / DISCERN / SMCS +RMM - best error-controlled comparator per regime | -2.83 / -3.16 / -3.71 (all CI < 0) |
| same, comparator restricted to protocol's anytime class (audit) | -3.84 / -4.17 / -4.71 |
| Gated / DISCERN / SMCS +RMM - P7s (ours, prior) | -0.61 [-1.86,+0.57] / -0.94 [-2.42,+0.65] / -1.49 [-3.02,-0.01] |
| LRMD - best error-controlled comparator | -5.40 [-6.53, -4.35] |
| LRMD - P7s | -3.18 [-4.67, -1.69] |
| LRMD - best method of any kind (incl. unsafe selectors) | +12.69 [+10.97, +14.41] |

Per regime, the wrapped methods lose to front-loaded Gated on V_better_p70 (+16 to +21) and
V_late_1400 (+1.7); the family win is carried by four late-change regimes.

## 5. Real-data validation

Nine replay streams (168 episodes x 20 replay seeds), all previously exposed, none with a
within-stream sign change. RMM lowers DISCERN's cost significantly on rialto, ldpa, airlines,
criteo and Gated's on ldpa, but raises Gated's on rialto (+3.9) and bank (+4.1). Against the
strongest error-controlled comparator the wrapped methods win on 0/9 streams; LRMD wins only on
weather (K=3) and loses on bank. **Real-data generalisation of the SOTA claim is not
established.** The five-independent-case-study target was not met.

## 6. Ablations

Restart mixture: Gated+RMM - single start = -4.0 [-5.3,-2.7] on validation (all from late
change; single start is cheaper on stationary alternatives). Post-verdict acquisition: -2.5
[-4.1,-1.0], and it drives the dependence failure (rho=.8 promotion .10 without, .24 with).
Restarting the base: no effect (386.45 vs 386.49 dev) — the detector does the work, so the
"attachable" framing is largely a way of adding the detector to an existing certificate.
Horizon pacing in LRMD: +0.49 (ns) on validation. LRMD start-prior vs single start: -3.80
[-4.64,-3.00].

## 7. HKUSTDial / ARIS review

Canonical `experiment-audit` and `result-to-claim` SKILL.md files are not installed on this
machine (earlier runs used `C:/Users/nigel/.claude/skills` through Codex). Two fresh-context
Claude subagents performed the roles, each recomputing from raw records. They share the
executor's model family; independence is **not** verified. Trace metadata:
`.aris/traces/atlas-v2/2026-11-03_run01/`.

* **Experiment audit: PASS WITH ISSUES.** No leakage, pairing, seed, budget or arithmetic
  errors; all 116,500 rows satisfy the cost identity; every primary number reproduced. MAJOR:
  primary family named after development; the Wilson criterion fails a nominal-level method
  with probability ~.56 (LRMD's fresh-seed null rate .032); dependence. MINOR: run count (fixed),
  comparator class wider than protocol (conservative), the front-loaded comparator keeps range
  20 — a correctly ranged `gated_LCE_front` cuts the margin by ~0.5 on scratch seeds but the
  claim survives; two development rows omitted (fixed); alpha after the first promotion not
  fully controlled (doc corrected); real-data units are correlated consecutive windows.
* **Result-to-claim: claim_supported = partial.** Supported: base improvements, family-average
  win over the adapted error-controlled comparator, independent-null safety, LRMD's registered
  safety failure. Unsupported: per-regime superiority on stationary improvement, a clear margin
  over P7s for two of three bases, any real-data SOTA claim. Novelty: the detector is a
  Shiryaev-Roberts/e-detector mixture (Shin-Ramdas-Rinaldo; Saha-Ramdas) on label-clock
  outcomes plus observation control; incremental as a method, with the atlas diagnosis possibly
  the stronger contribution. "Not yet a competitive algorithmic paper."

## 8. Research positioning (the claim we accept)

Under T=2000, B=200, c_q=.05, c_s=5, alpha=.05 and an independent conditional null, attaching
a restart-mixture label-clock e-detector with continued acquisition (RMM) significantly lowers
the net cost of Gated-deployment, DISCERN-style and SMCS-adapter deployment on frozen synthetic
late-improvement and stationary-better regimes, keeps independent-null false promotion at .01
(Wilson UB .05), and on that family average beats the best adapted error-controlled comparator
by 2.8-3.7 cost units. The gain comes from late-change regimes. It is not SOTA on strong
stationary improvement (front-loaded Gated is better), not clearly better than our prior P7s
for two of three bases, raises false promotion to .23-.24 under Markov dependence (rho=.8),
raises cost on transient/reversal/recurrent changes, and shows no real-data advantage on nine
previously exposed streams.

## Next bounded action

Register and run the decisive test the claim reviewer named: fresh, unexposed real streams with
a genuine within-stream improvement (e.g. a challenger retrained on recent data that overtakes
the incumbent partway), with P7s, front-loaded Gated and correctly ranged `gated_LCE_front` in
the controlled set. If RMM/LRMD does not beat them there, drop the method claim and write the
atlas diagnosis instead. Second priority: a dependence-aware detector (block or Markov-aware
betting). LRMD may be re-registered with a corrected safety criterion (e.g. n >= 600 null seeds)
on new seeds; it must not be re-scored on these.
