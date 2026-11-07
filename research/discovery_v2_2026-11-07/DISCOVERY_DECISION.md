# Discovery decision, 2026-11-07 (success criteria v2)

Governing standard: `docs/research_success_criteria_v2.md`. Candidate tracking:
`research/candidate_registry_v2.md`. The decision rule applied below is the one frozen in
`P2_CONTROLS_REGISTRATION.md` (commit 9abfc5c3, made before the full run). Every number below comes
from `outputs/p2_controls_rates.csv` and `outputs/p2_controls_verdicts.json` in this folder. The run
provenance is in `outputs/discovery_v2_p2_controls/RUN_RECORD.md`: 4 conditions × 52,080 records,
rc=0 throughout, no warnings. That outputs directory is not committed.

## 1. P2 attribution controls: results against the frozen hypotheses

Ten certified ports were tested; xu_acquisition_only was excluded as registered. Each cell is one
dataset × policy. A "break" means a promote rate above 0.0936 whose split-cluster bootstrap lower CI is
above 0.05.

| condition | what it keeps | certified ports breaking on ≥1 dataset | broken cells | mean / max promote | mean / max harmful promote |
|---|---|---|---|---|---|
| ORIG | fixed effect + dependence | 9 / 10 | 25 | .121 / .428 | .0098 / .072 |
| PERM | fixed effect only | 9 / 10 | 11 (appliances, bike, household) | .082 / .292 | .0001 / .0017 |
| BSWAP | dependence only | 7 / 10 | 15 (all 5 datasets) | .068 / .242 | .0084 / .069 |
| ESWAP | exact conditional null | 0 / 10 | 0 | .003 / .040 | .0003 / .008 |

* **HP2-b (validity under the exact null): HOLDS.** Under ESWAP every certified port's upper CI is
  ≤ 0.0936; the largest promote rate is SMCS on beijing at 0.040 [0.013, 0.079]. The ORIG breaks are
  therefore not explained by a broken implementation that fails even when exchangeability holds per
  event. This also answers the most damaging possible reading of the adversarial review.
* **HP2-a (pure fixed effect, PERM/ORIG ≥ 0.75): FALSE.** The mean ratio is 0.637 over 25 cells. Removing
  serial dependence reduces the breaks but does not account for them.
* **HP2-c (dependence suffices, ≥3 of 10 ports break under BSWAP): TRUE.** 7 of 10 ports break. Beijing
  shows it most clearly: SMCS gives ORIG .219, PERM .071, BSWAP .231.
* **Frozen decision rule:** HP2-c true ⇒ **the serial-dependence framing survives.**
* **Not anticipated by the rule:** PERM still breaks 9/10 ports. So the per-split fixed effect is also
  sufficient on its own, mainly on appliances. The supported statement is that **both mechanisms
  independently drive certified gates past the marginal bound, and their mix differs by dataset.** The
  review's confound was real, and it now has a measured split rather than a single explanation.

### Exploratory finding, surfaced here (not registered as a hypothesis)

The harmful-promotion column (promote with realised advantage ≤ 0) was computed by the pre-committed
analysis script. No hypothesis was frozen on it, so per v2 §4 this finding is **EXPLORATORY**.

* Breaks driven by the fixed effect are nearly harmless: under PERM, harmful promotion averages .0001
  and is at most .0017.
* Breaks driven by dependence carry real harm: under BSWAP it averages .0084 and is at most .069
  (SMCS on appliances).
* The harmful share of promotions is 0.067 under BSWAP and 0.001 under PERM.

Reading: when the challenger really is better on that split (the fixed effect), "violating" the
marginal null mostly promotes a beneficial model. That is a null-class mismatch, not decision harm. When
dependence alone drives the gate, the promotions are frequently wrong. This is exactly the estimand
separation AGENTS.md asks for: a marginal false-promotion rate conflates the two, while
conditional-harm accounting separates them. This must be frozen and confirmed before it is claimed.

## 2. The most promising paper buildable now

**Working title:** *Known-null stress tests for certified model-deployment gates: serial dependence and
split-level effects as separable failure modes.*

* **v2 class: B (promising paper), with C (workshop / datasets-and-benchmarks track) as the safe floor.**
  The review rated it D→C before the controls. The controls remove the invalid-implementation
  explanation (HP2-b), keep the dependence mechanism (HP2-c), and add a decision-relevant
  harm/no-harm split. That justifies B. It is not A: the evidence is exploratory on exposed streams,
  there is no untouched-data confirmation, and the comparators are common-contract ports.
* **v2 minimum success:** Option B (benchmark: a reproducible ranking/validity inversion with practical
  consequence) and Option C (empirical behaviour of SOTA gates under realistic dependence) are met at the
  **exploratory** level.
* **Narrow claim supported today (EXPLORATORY):**
  * On five UCI chronological regression streams with exchangeable-twin challengers, nine of ten
    common-contract ports of certified deployment gates exceed their nominal marginal false-promotion
    bound.
  * Both serial dependence alone (BSWAP) and the per-split fixed effect alone (PERM) reproduce the
    exceedance.
  * Under a per-event exact conditional null (ESWAP), all ten respect the bound.
  * Uncertified selectors (Model Picker .695–.931, CAMS .788–.962) promote on most nulls under every
    condition.
* **Contributions:**
  1. the twin known-null protocol with four attribution controls, as a reusable stress test;
  2. the measured decomposition of exceedance into fixed-effect and dependence parts;
  3. the (to-be-confirmed) finding that only the dependence part translates into harmful promotion;
  4. the comparison of the certified ports with uncertified selectors.
* **Claims it must not make:**
  * that the SOTA methods are invalid in their own stated null class (they assume exchangeability or
    i.i.d. conditions that these streams violate);
  * native-implementation results;
  * superiority of A5b (it failed K2 on bike_hour, 0.058 [0.017, 0.100], and is not part of this claim);
  * generalisation beyond these five streams and this twin construction.

### Remaining tests, in order of value

1. **Freeze the harmful-promotion hypothesis** (PERM harm ≈ 0, BSWAP harm > 0, with thresholds) and the
   block length. Then confirm it on fresh splits or on new datasets that this programme has not touched.
2. **Code-fix replay.** Re-run ORIG and BSWAP with the codex/sprint2-leaderboards fixes c66185c0 and
   81dc4d34 for the five MOPE-affected gated ports. Until then, those five ports carry an explicit caveat.
3. **Block-length sweep for BSWAP** (for example 10/50/100/500) to show that harm scales with dependence
   range. This is a dose–response check, not tuning.
4. **Uncertainty.** Add an evaluation-stream block bootstrap alongside the split-cluster bootstrap. Give
   harmful-promotion CIs in every table (`harmful_hi` exists; lower bounds are needed).
5. **Author-code comparators** where they exist (SMCS, Choe–Ramdas), to remove the common-contract
   caveat for at least two methods.
6. **Prior-art check** (source-auditor) on dependence-robust anytime-valid testing (blocked or
   mixing-adjusted e-processes) and on known-null benchmarks for deployment gates. Novelty is UNVERIFIED
   until this is done.

## 3. Supporting and secondary candidates

| candidate | v2 class | role |
|---|---|---|
| P1 — RMM / conditional excess-cost monitoring | B/C | second paper; shares the conditional-vs-marginal estimand theme |
| E_srr ranking inversion | D | benchmark observation; can be an appendix of P2 |
| P6 vs P3b | D | empirical comparison; reported where it applies |
| H2c guide-alignment counterexample (X3 MAG) | E (MAG) / D (counterexample) | H-MAG-1 failed; the gas in-sample reversal remains a documented counterexample, `X3_MAG_RESULTS.md` |
| DP direction | abandoned | killed earlier on the evidence recorded in the registry |

## 4. Integrity notes

* All P2 streams were previously exposed (EXPLORATORY). None of this is independent confirmation.
* The five MOPE-affected ports ran on HEAD code without the leaderboard fixes.
* Every dataset tested is reported. Metro barely triggers any port in any condition. That is a
  limitation (low power on that stream), not a removed result.
* Figures: AGENTS.md requires PaperBanana. **PaperBanana is not available in this environment**, so no
  figures were produced and no substitute generator was used.

**Assessment: CONTINUE** with P2 as the lead paper (class B, exploratory), starting with remaining tests 1–2.
