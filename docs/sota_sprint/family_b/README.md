# SOTA sprint family B: nonstationary detection and recovery (screening, dev seeds)

Status: development screening only (20 dev seeds, seed base 2026110501; null check 300 seeds at
2026110512). These are descriptive screening results, not confirmatory evidence. Code:
`scripts/sota_sprint/fam_b.py` (`RecoveryMonitor`, subclass of the Atlas v2 RMM host). Tests:
`tests/sota_sprint/test_fam_b.py` (22 pass). Ledger: `ledger.json`; per-family numbers:
`key_numbers.json`; analyze.py output: `screen1.json/.md`.

## Host and what is controlled

Host = `rmm:gated_deployment+RMM`. `B0_host` (all mechanisms off) reproduces it exactly: identical
net cost and deployment path on all 240 dev jobs.

* **First promotion** (all B variants): base Gated CS at alpha/2 plus the label-clock restart-mixture
  SR e-detector at alpha/2. Under the iid conditional null (challenger correct on a queried
  disagreement with probability <= 1/2, independent of the past) P(any promotion) <= alpha = .05.
  Reserve and deadline only change predictable query rules, and the detector uses unweighted
  label-clock outcomes, so this bound is unchanged. Empirical: F0_null 1-3/300 promotions.
* **After the first promotion**: the B2 rollback is a detector alarm at alpha_rb = .10 against
  "the deployed challenger is not worse". A false rollback is a cost (2 c_s plus time on the
  incumbent), not a safety error; observed false rollbacks: 0 on F0_better/F9_bursty_better, at
  most .05-.10 per run on F4_recurrent. Re-promotions after a rollback spend (alpha_base +
  alpha_det)/2^k. **Not controlled**: detection delay/time on a model that has become worse;
  anything under serial dependence; the host's own rollback detector in B1/B3/B4 (alpha=.05).
* **Dependence (rho=.8) null fails for everyone in this line**: F5_dep_null_r8 promotion on 300
  seeds: host .150, B2 .150, B5 .123, B6 .150, B2+B4 .170 (bound .0936). No B mechanism addresses it.

## Results (20 dev seeds; family = per-seed mean of paired differences; 95% t-interval)

Families: late = F1_late_800, F1_late_1200, S_late_1500; reversal = F3_reversal_800,
S_reversal_400; recurrent = F4_recurrent; transient = F2_transient, S_transient_short;
stationary_alt = F0_better, F9_bursty_better. Negative favours the candidate.

| cand | late vs host | reversal vs host | recurrent vs host | stat_alt vs host | reversal vs best cert | recurrent vs best cert | late vs best cert |
|---|---|---|---|---|---|---|---|
| host | 0 | 0 | 0 | 0 | +28.5 [+16.6,+40.4] | +21.7 [+13.3,+30.1] | -10.6 [-14.2,-7.0] |
| B1_r10 | +4.4 [+0.9,+8.0] | -6.7 [-15.2,+1.9] | -3.4 [-7.2,+0.5] | +10.7 [+4.1,+17.3] | +21.8 | +18.4 | -6.2 |
| B1_r15 | +3.3 [-1.8,+8.4] | -9.2 [-20.9,+2.4] | -6.9 [-12.4,-1.3] | +7.9 [+1.4,+14.4] | +19.3 | +14.9 | -7.3 |
| B1_r25 | +5.0 [+0.7,+9.4] | -17.1 [-27.2,-7.0] | -14.7 [-22.9,-6.6] | +17.3 [+7.7,+26.9] | +11.4 | +7.0 | -5.6 |
| **B2** | 0 (identical) | **-8.2 [-11.7,-4.7]** | +2.0 [-2.3,+6.2] | 0 (identical) | +20.3 [+9.5,+31.1] | +23.7 | -10.6 |
| B3 | +1.3 [+0.5,+2.1] | +0.0 [-5.9,+6.0] | -3.0 [-9.6,+3.7] | -4.6 [-8.2,-1.1] | +28.5 | +18.8 | -9.3 |
| B4 | -0.8 [-3.2,+1.6] | -3.5 [-10.1,+3.2] | -3.5 [-8.1,+1.1] | +0.5 [-2.3,+3.3] | +25.0 | +18.2 | -11.4 |
| B5 | +3.4 [-2.0,+8.9] | -16.0 [-26.2,-5.8] | -6.7 [-12.2,-1.2] | +7.1 [-0.5,+14.6] | +12.5 [+2.3,+22.7] | +15.0 | -7.2 |
| B6 | +4.7 [-0.8,+10.1] | -11.1 [-22.2,-0.0] | -4.9 [-11.2,+1.4] | -0.0 [-5.8,+5.7] | +17.4 | +16.8 | -5.9 |
| B5-reserve (=B2+B4) | -0.8 [-3.2,+1.6] | -9.7 [-15.1,-4.2] | -4.2 [-8.8,+0.4] | +0.5 [-2.3,+3.3] | +18.8 | +17.5 | -11.4 |
| B5-rollback (=B1+B4) | +3.4 | -8.5 [-19.1,+2.2] | -6.9 | +7.1 | +20.0 | +14.8 | -7.2 |
| B5-deadline (=B1+B2) | +3.3 | -17.4 [-28.9,-5.9] | -7.1 | +7.9 | +11.1 | +14.7 | -7.3 |

Best certified on reversal/recurrent regimes is `discern_design_floor` (it rarely promotes);
`CONTROL_never_switch` is cheaper still on every change regime screened. Transient: B4 and
B2+B4 are worse than host by +3.6 [+0.3,+6.9]; others are ns.

Path diagnostics (`fam_b.py diagnose`, replay verified identical to screen nets): on
F3_reversal_800, correct rollbacks per run host .75, B2 .90, B2+B4 .95, B5 .60; mean events from
reversal to rollback (censored at T when none) host 785, B2 614, B2+B4 507, B5 538. False
rollbacks 0 for every candidate on stationary alternatives.

Stationary price (net minus never-switch on F0_null; mostly label spend): host +10.0, B2 +10.0,
B4 +9.4, B1 +7.5 to +9.0, B5/B6 +8.4. Dynamic regret vs expected-cost oracle (reversal family):
host 82.8, B2 74.6, B2+B4 73.1, B5 66.8 (see `key_numbers.json`).

## Interpretation

* Rollback speed is capped by the label rate: ~1 queried disagreement per 10 events at B=200 and
  ~0.08 nats per label, so even B2's cheaper rollback threshold needs ~500 events after a reversal.
  B2 recovers ~170 events of that; it cannot recover the cost of a first promotion that typically
  arrives at t~550 (the host promotes late, so there is little gain to protect before t=800).
* The reserve (B1, and B5/B6 through it) "helps" reversal mainly by suppressing promotion
  (promotion .70 vs 1.0 on F3), which is why it costs on late and stationary improvement. The
  mechanism ablations confirm this: removing the reserve from B5 halves the reversal gain and
  removes the stationary/late cost.
* Multiscale restarts (B3) and deadline-aware acquisition (B4) do not move reversal or recurrent
  costs; B4's useful-window reallocation is ~8% of the horizon at T=2000, delay=100.
* No B candidate beats the best certified published comparator on reversal or recurrent regimes;
  all inherit the host's late-change advantage (-6 to -11 vs best certified).

## Disposition

Continue (scoped): **B2** as the rollback component of the RMM line: zero cost before
promotion, significant reversal gain over the host, no false rollbacks seen, same null rates as
host. Second: **B2+B4** (`B5-reserve`) only as a variant to re-check; its transient cost is
significant. Pivot: pair B2 with a host that promotes earlier (front-loaded Gated) so there is a
gain to protect, and address the rho=.8 failure separately. Stop: B1, B3, B4, B5, B6 as proposed.

Limitations: 20 seeds per regime; best-certified selection per regime on the same seeds (favours
the comparator); the B5/B6 reserve level (.15) was fixed before screening; runtime mean ~0.2 s,
max 1.34 s per episode.
