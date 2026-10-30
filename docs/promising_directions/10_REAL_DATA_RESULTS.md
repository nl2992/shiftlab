# 10 Real-data results (2026-10-30)

## 1. Statement

**No new real-data run was made in this programme.** A1, B1 and B2 are synthetic (`results/a1/`, `results/b1/`, `results/b2/`). Everything below is inherited, descriptive, and drawn from the audit documents; paths are relative to `docs/promising_directions/`. No inherited real-data number here is confirmatory.

## 2. Inherited exposed results

| Dataset | Result | Status | Source |
|---|---|---|---|
| UCI Gas sensor | Challenger errors 3403 -> 2983 over 7977 observations = 12.342% gain | VERIFIED (recomputed in the audit) | `00_REPOSITORY_AUDIT.md` section 2; `01_EVIDENCE_MATRIX.md` Lane A |
| UCI Gas sensor | Clairvoyant batch switching 2955 vs always-challenger 2984 = 0.972% headroom (switch cost 1, no label cost, exposed holdout) | DOC-ONLY | same, citing `docs/exhaustive_evaluation/PROMISING_OPTIONS_EXPLORATION.md` @ `ad6cedf` |
| Bike, Beijing | No headroom; raw data absent locally (URLs only) | DOC-ONLY (headroom); NOT FOUND (raw data) | `00_REPOSITORY_AUDIT.md` section 2 |
| CRSP | Exposed retrospective stress data. RPOQ growth vs uniform -1.15 [-1.56, -0.76] at 5% and -3.21 [-5.16, -0.87] at 20% log-wealth. CRSP dates are not causal change labels or point-in-time publication timestamps | DOC-ONLY | `01_EVIDENCE_MATRIX.md` Lane D, section 2 |
| Gas D2 replay | H2c alarms 242-824 events later than cost-only Kelly/ONS, with 2-4x excess cost before alarm; reverses the synthetic G5 gain | DOC-ONLY, exposed holdout | `01_EVIDENCE_MATRIX.md` Lane B and section 2 |

Reading: the large Gas challenger gain (12.342%) is predictive headroom of the challenger over the incumbent. The headroom that switching can capture under a switch cost is 0.972%, which is the figure relevant to a switching or certification policy. These must not be conflated. Gas is an exposed holdout, so neither number supports a confirmatory claim.

## 3. Local data inventory (`00_REPOSITORY_AUDIT.md` section 2)

Present in `shift-research-starter/data`: criteo_privatead (32.5 GB), CRSP CIZ (2.6 GB raw + 2.6 GB processed, licensed, per-year SHA manifests), criteo_attribution, eia, folktables, wilds, opsd, monash, open_bandit, noaa, upworthy, gas_sensor (`uci-224.zip` + receipt), hillstrom, elec2, binance, fred. Sizes are stated only for the three marked. Not present: Bike and Beijing raw data. The audit did not assess whether any of the other datasets has candidate headroom, paired-loss structure or label-release timestamps; this file makes no claim about them.

## 4. Controller rule

IF no admissible real dataset has useful candidate headroom THEN report the task limitation.

Current application: the only datasets with recorded headroom numbers are Gas (12.342% challenger gain but 0.972% clairvoyant switching headroom, exposed) and Bike/Beijing (none, raw data absent). CRSP is stylised and exposed. No dataset in the audit documents is both admissible (unexposed, with defensible chronology and label timing) and shown to have useful candidate headroom. **Task limitation: real-data evaluation of P3b is not supported by any dataset recorded in the audit documents.** This is a statement about the audited data inventory, not evidence for or against P3b on real data.

## 5. Audits required before any real-data run of P3b

These are requirements, not results. None was performed.

1. **Action-headroom audit.** For a pre-stated incumbent and challenger, compute on a development window (not the final test window): challenger gain over incumbent, clairvoyant switching headroom with the intended c_s and c_q (as in the Gas 0.972% figure but with label cost included), and the share of events on which the two models disagree. P3b only acquires labels on disagreements (structural zero on agreement; `05_PAIRED_CERTIFICATION_THEORY.md`), so a dataset with low disagreement or low switching headroom cannot show a gain. State a go / no-go threshold before looking at the test window.
2. **Chronology audit.** Chronological splits only; label-availability timestamps and delay law documented per `AGENTS.md`; out-of-order, missing and selectively sampled feedback represented explicitly; the B1/B2 fixed delay of 5 is a synthetic assumption and cannot be assumed. Both action losses must be identifiable from observed outcomes, or a causal or off-policy design must be stated.
3. **Leakage audit.** Train-only preprocessing; no test-window information in the incumbent, challenger, bet, pacing or threshold design; checksums and provenance recorded for every raw file; Gas, CRSP, Bike and Beijing results already exposed in this repository cannot serve as an unexposed holdout.
4. **Dependence check.** P3b validity in `05_PAIRED_CERTIFICATION_THEORY.md` is a fixed-delay conditional-null argument. Real streams are dependent; HG fails under dependence (FAR up to .23) and the depgate necessary-condition bound alpha + eps(1 + (T-1) delta) applies (`01_EVIDENCE_MATRIX.md` Lanes C and D). Report empirical FAR as empirical.
5. **Evaluator-side truth.** Do not infer shift times or application utilities from alarms or convenient cost settings (`AGENTS.md`). CRSP specifically: retrospective stress test only.
6. **Baselines.** The missing comparators listed in `07_MATCHED_BASELINE_COMPARISONS.md` section 3.

## 6. Most plausible candidate dataset and blocker (audit documents only)

Gas sensor (UCI-224; local `gas_sensor` with `uci-224.zip` and receipt) is the only dataset in the audit documents with a positive recorded challenger gain, and it is present locally. Blockers recorded: (a) it is an exposed holdout, so no confirmatory use; (b) the clairvoyant switching headroom is only 0.972% with switch cost 1 and no label cost (DOC-ONLY), so adding label cost can only reduce it; (c) the D2 replay shows H2c later than cost-only Kelly/ONS on it (DOC-ONLY). Bike and Beijing show no headroom and their raw data is absent. The audit documents do not identify a better candidate. Unexamined datasets in the inventory (for example open_bandit, elec2, folktables, wilds) have no recorded assessment here and nothing should be inferred about them.
