# Failure Atlas v2: independent discovery and algorithm review (native substitute)

Reviewer: fresh general-purpose subagent, 2026-11-03, read-only repo access, recomputed numbers from
raw records with its own scripts (`.../scratchpad/review1/`). The canonical HKUSTDial/ARIS
`experiment-audit` and `result-to-claim` skills are not installed on this machine or in the plugin
catalog; this is a native substitute, not a cross-family ARIS review. Same model family as the
author. Recorded verbatim in substance; condensed formatting.

## Verdicts

1. Comparator fidelity: **FAIL**. Two of four hosts weakened by adapter choices not covered by the fidelity record. Pairing is correctly implemented.
2. Validity: **PASS with caveats**. QCE/QSG valid under the pointwise conditional null; QSG docstring argument wrong but conclusion holds; the guarantee does not cover the stationary-mean nulls used to define "certified".
3. Mechanism: **PARTIAL**. Pacing latency supported; range dilution only for gated/DISCERN and from an adapter choice; "shared across >= 3 independent families" not supported.
4. Novelty: **LOW**.
5. "SOTA within the certified class": **not yet defensible**.

## Defects

CRITICAL
- C1. M1 lives in a shared adapter component, not the published methods: gated/DISCERN use `PacedDisagreementAcquisition` (controls.py:28-47); SMCS uses the P7a/B3+ pacer (smcs.py:234-259); P7s is ours; Xu's evidence uses `b1.bet_from_stats` (ours). No paper prescribes a hard-budget pacer; gated and DISCERN are one family in SUITE_INFO.
- C2. Range dilution is an artifact of a declared worst case: DISCERN fixes `c = 1/p_min = 20` (certificate_stops.py:510), gated fixes `wmax = 20` (:578), although the frozen `q_t` is predictable, so `c_t`/`wmax_t = 1/q_t` or a design `pi_min` is legitimate. DISCERN never promotes even at B=1000 (0/60) and on none of the 20 synthetic cells: a straw man. "DISCERN+QCE" is a re-declaration of the range to 1.
- C3. Certified class defined empirically and the bar moved: dev null promotion at F5_dep_null_r8 / r95: QSG v1 .24/.63, gated+FLQ .08/.37, SMCS+FLQ .16/.41, gated .00/.02, DISCERN .00/.00, SMCS .07/.34, Xu .07/.28, P7s .09/.38 (bound ~.094). Amendment 1 demoted rho=.8 to "stress" after seeing dev.

MAJOR
- M-a. Xu "range dilution" claim false: `lambda <= q/2` on `d/q` is a bet <= 1/2 on `d`; QCE alone does nothing for Xu (+2.7 dev; 388.0 vs 387.2 budget experiment). SMCS's host factor already equals `1 + d/2`; its "QCE" is just an aGRAPA bet.
- M-b. gated and DISCERN are absent from SOTA_IMPLEMENTATION_VALIDATION.md (no fidelity record for the hosts with the largest gains).
- M-c. Real data: seeds vary only policy randomness (pseudo-replication); spam K=1, uci K=4, weather K=3, elec2 K=4; `real_repair` used the discovery seed base and QSG v0 (rerunning 18 rows with current code changed 5).
- M-d. Regressions understated: FLQ - host on dev F3_reversal_800 gated +60.9, DISCERN +64.5, Xu +21.4; F4_recurrent +16.6/+14.4/+10.3; F2_transient +7.3/+7.6/+5.4. QSG v1 - best published certified: F3_reversal_800 +49.0 [44,54], F4_recurrent +21.8, F2_transient +9.6, F1_late_800 +5.3, F5_dep_null_r95 +7.5.
- M-e. Primary validation outcome near-tautological (six stationary alternatives chosen after dev showed front-loading wins there).

MINOR
- QSG docstring (qsg.py:13-15) wrongly calls E_k a supermartingale; correct: `E_k + 1/(k+1)` is a test supermartingale starting at 1, so Ville still gives level a; alpha/2^cycle union over fresh segments valid.
- SMCS front-loading keyed on `members[incumbent]` keeps q=1 after challenger exclusion.
- selected_mechanism.md overstatements: "+30 to +120 on every stationary cell" false (F8 SMCS +10; F7_near_tiny +8); "QSG best certified on every stationary cell" false (F7_near_tiny QSG - SMCS +1.1 [0.1, 2.3]); real M1 framed against Online LLM Picker; vs strongest certified (SMCS) gaps are +44 spam, +35 openml, +14 uci, +17 rialto.
- Budget experiment confounds q with label count and HT variance.

Fine as claimed: pairing (same stream per regime/seed across policies), MRO and overrides of the QCE mixin, request-order ingestion, no label leakage into query rules.

## Novelty judgement

Querying every disagreement is DISCERN's own design with pi=1; testing unweighted queried outcomes is a sequential sign/McNemar test on discordant pairs (optional skipping); the started mixture is close to e-detectors (Shin, Ramdas, Rinaldo) and alpha/2^j is standard spending; Online LLM Picker already front-loads. (Reviewer's own knowledge; no web search.) Surviving contribution: the harness and the documented observation that budget-uniform pacing plus a worst-case HT range slows certification.

## Required before claiming anything

1. Re-port gated/DISCERN with predictable per-step range or a declared design `pi_min`; add fidelity entries.
2. Tuned non-uniform acquisition baselines for every host.
3. One certification criterion fixed before validation, dependence nulls reinstated.
4. Real data rerun on fresh seeds with QSG v1, episode-level CIs, small-K datasets out of the powered set.
5. Reframe M1 as a property of the acquisition adapter; put reversal/recurrent/transient regressions in the headline.

## Author response

Items 1, 3, 4 and 5 adopted in protocol Amendment 2 (before reading validation rows); the SMCS
front condition and the QSG docstring were corrected. Item 2 is partly covered: every host has a
front-only arm; a "q = .5 over the first half" arm was not run. The novelty judgement is accepted:
FLQ is a recombination of known ingredients and is claimed, if at all, as an empirical repair.
