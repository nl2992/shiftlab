# Refinement round 2: revised proposal and claim-by-claim response

**Recorded 2026-10-28, loop tick 8.** This round responds to `ADVERSARIAL_REVIEW_1.md`, a Codex
`gpt-6.1-sol` xhigh review with five accepted fatal objections. The problem anchor is unchanged
from round 1.

**Status labels:**
- [established]: a frozen, verified result or a published theorem;
- [lemma]: an exact derivation with a proof sketch given here;
- [hypothesis]: an untested empirical prediction;
- [heuristic]: an engineering rule.

## Revision log (claim by claim)

| R1 item | Objection | Change in round 2 | Status |
|---|---|---|---|
| Null | **F1:** the proposal conditioned on current `X_t`, but the charter conditions on `F_{t−1}` only, and the stationary controls violate the stronger null | The primary null is the **charter's conditional-on-past null** `E[Z_t − ε \| F_{t−1}] ≤ 0`. The current-context null is dropped. The existing controls are labelled as satisfying the past-conditional null, not the current-context null. An arm-by-arm validity table is added (§4). | Resolved by restatement |
| Proposition S | **F2:** the corollary overreaches; **majors:** PPI breaks invariance; adaptive engines are outside it; the ε remainder can be large in relative terms; the reserve stop does not preserve allocation equivalence | Demoted to a **restricted, credited Lemma L** (§3): label-time wealth invariance for zero-anchor HT with fixed-fraction stakes at ε = 0, given the ordered labelled losses. It includes the stake-grid mixture and an exact ε remainder bound. An **applicability table** lists counterexamples for PPI (`log(1+c/(2−q))`) and states that adaptive engines are outside it. **The calendar-time corollary is removed.** | Resolved by narrowing |
| DISCERN positioning | **F3:** DISCERN §6.4 already runs head-to-head experiments of gating against uniform, PPI-style and active-testing baselines on identical streams | **Lead-verified (Haiku fetch of §6.4, a summarised page, to be confirmed against the PDF before citing).** DISCERN §6.4 compares DISCERN, uniform, PPI-style and active-testing labelling on identical real streams with a Waudby-Smith–Ramdas EB CS, measuring labels-to-verdict. Section 6 has **no** asymmetric decision costs, hard label reserve, intervention, rollback or fallback, or adaptive betting-engine panel. Drift appears only in §6.5 (a windowed CS) and a burst experiment. **H1 and H2 are re-positioned as replications of DISCERN's gating economics** under decision costs, finite reserves and non-stationary incumbent monitoring, not as findings of their own. | Resolved by crediting |
| H4 | **F4:** the comparison is confounded by stage timing (candidates deploy from event 2,400; the monitor window closes at 1,600, when native adaptation starts) and by rollback asymmetry | H4 is restated as a **descriptive finding about the frozen state machines** (§2). The attribution to reference safety is withdrawn. A **matched-opportunity factorial** (E3) is added to test what governs intervention rankings. | Resolved by restatement plus a new test |
| Claim A | **F5:** the two-factor explanation is overgeneral; "every screened mechanism failed" was overstated | Claim A is replaced by the bounded, contract-centred **Claim B** (§1). The screened set is named (stratified allocation WP2, data-efficient controller WP3, ADG anchor, integrated controller). Positive component results (Target-Scout, PPE) are kept in their own panels. | Resolved by narrowing |
| H1 metric | "Growth" is a per-stream best-fixed-stake post-onset diagnostic; gated HT versus uniform PPI changes acquisition, anchor and bound together | H1 is renamed **"registered post-onset best-fixed-stake growth diagnostic"**. E2 adds **uniform HT with the same engine** and reports deployed mixture log-wealth. | Addressed by a new test |
| Matching | "Matched" was undefined | §5 defines four levels: common access, identical feedback replay, common resource cap, and matched realized spend. Each comparison is tagged. | Resolved |
| Evidence status | S3 is development evidence; H4 contrasts are outside the frozen 22-test family; a degenerate bootstrap interval | S3 is labelled **development**. Confirmation must come from E2 and E3 on fresh registered seeds. The H4 contrasts are labelled **post hoc**. P2 is reported by exact McNemar only. | Resolved |
| E1–E3 | E2 is endogenous; E3 conflated label time with calendar time; a margin without power cannot show equivalence | E2 now uses fixed-window quantities and held-out cross-cell prediction. Lemma L is checked exactly on common ordered loss sequences (deterministic). Calendar-time comparisons use pre-registered TOST equivalence with a power calculation. | Resolved in design |
| Multiplicity | Families were compressed | §5 table enumerates them. | Resolved |
| D&B value | The benchmark needs a reusable contract | §6 adds a benchmark-contract deliverable. | Added |
| Real-data scope | Only EIA, with imposed costs and exposed paths | **Unresolved; needs the user.** A second task with identifiable paired costs on a locked, unused split. The only candidate without new acquisition is **post-freeze EIA**, which needs an API key or a bulk pull. See §7. | Blocker |

## 1. Dominant claim (revised)

**Claim B.** We give a reusable, matched-resource evaluation contract for paired decision-harm
monitoring and intervention. On its registered synthetic generators and the imposed-cost EIA
reserve task, it yields three reproducible findings that the current literature does not report
together:

1. **Gating replicates under decision costs.** DISCERN's disagreement-gating label economics
   carry over to asymmetric-cost paired harm with finite reserves and non-stationary incumbents.
   Gated HT detects earlier than ungated uniform estimators at comparable realized spend. This is
   **credited to DISCERN**; our contribution is the replication under the decision-harm contract.
2. **Fixed beats paced under bursts.** Under bursty post-onset disagreement, fixed-rate gating
   detects no later than a past-only paced rule. This is in S3 R7 and on EIA [established,
   development]; fresh confirmation is in E2.
3. **Intervention design sets the ranking.** In current integrated pipelines, the ranking of
   intervention rules is sensitive to response latency, monitoring coverage and rollback
   availability. A naive monitor-then-revert rule beats a certification pipeline by 4–6× on three
   profiles and loses by 8× after a reversal [established descriptively for the frozen state
   machines]. Which factor governs the ranking is tested in E3.

**What Claim B does not say:** that any new mechanism is better; that the findings transfer to
action-dependent feedback; or that the real-data panel is confirmatory.

## 2. H1–H4 restated

| ID | Restated finding | Evidence status |
|---|---|---|
| H1 | Gated HT against correctly bounded uniform PPI: registered post-onset best-fixed-stake growth ratio 7.20 [6.88, 7.55] at `r = 0.20`; exact McNemar 100/0, `p = 7.9e-31`, at `r = 0.05`. Comparable realized spend (118 against 114 labels, 177 against 171 dollars). **Credited replication of DISCERN gating.** | Development; checked against the artifacts by Codex |
| H2 | G1's analytic prediction is within a factor of two at all four budgets. This is consistent with DISCERN's Θ(1/ρ) (Thm 9), which is credited. | Development, pre-registered |
| H3 | Fixed ≥ paced: S3 `harmful_adaptation` 0.86 against 0.76 at `r = 0.10` (default mixture), and 0.94 against 0.91 under GRAPA. EIA fixed gating matches the full-feedback median delay in 10/10 detectable cells at each of `r = 0.05, 0.10, 0.20`. | Development and retrospective; descriptive; needs paired uncertainty (E2) |
| H4 | Frozen state machines: `q1_fallback` +664.6 / +685.9 / +448.0 against the full pipeline's +118.0 / +161.2 / 0 on three profiles; −1,148.5 against −143.8 after a reversal. **The arms differ in response latency (alarm against event 2,400), rollback availability and monitor-window coverage (native onset at 1,600 = window end).** | Descriptive, post hoc, confounded; tested in E3 |

## 3. Lemma L (restricted, explanatory, credited)

**Setting.** Zero-anchor HT increments `V_t = G_t Z_t / q_t − ε` on disagreement events, with
predictable `q_t ∈ [q_min, 1]`, a query coin conditionally independent of the outcome, `|Z_t| ≤ C`,
predictable bound `B_t = C/q_t + ε`, and stake `λ_t = c/B_t` with `c ∈ (0, 1)`.

**Lemma L [lemma].** Assume `ε = 0`. Fix the ordered sequence of labelled losses
`(Z_(1), …, Z_(n))`. Then the wealth after the n-th label is `∏_k (1 + c Z_(k)/C)`. It is
identical for every predictable propensity sequence, and unlabelled disagreement events contribute
factor 1. For a fixed-fraction grid `{c_j}` with weights `w_j`, the mixture wealth
`Σ_j w_j ∏_k (1 + c_j Z_(k)/C)` is likewise propensity-free.

*Proof sketch.* With `ε = 0`:
- an unqueried event gives `V = 0`, so its factor is 1;
- a queried event gives `λV = (c q/C)(Z/q) = cZ/C`.

With `ε > 0`, the per-label expected log-growth is
`E log(1 + c(Z − εq)/(C + εq)) + ((1 − q)/q)·log(1 − a)`, where `a = cεq/(C + εq)`. Its
deviation from the linearised form is
`R = ((1 − q)/q)(log(1 − a) + a)`, with `−(1 − q)a²/(2q(1 − a)) ≤ R ≤ 0`
(Codex's bound, accepted). **The relative error can be large when net growth is near zero.**

**Applicability table.**

| Engine or construction | Lemma L | Reason |
|---|---|---|
| Zero-anchor HT, fixed-fraction stake | Holds (ε = 0); bounded deviation for ε > 0 | Above |
| HT fixed-fraction stake mixture (default `PredictableBoundMeanEProcess`, `eprocess.py:154`) | Holds (ε = 0) | Mixture of propensity-free products |
| PPI anchor, bound `(C + ε)(2/q − 1)` | **Fails** | At ε = 0, deterministic `Z = C` gives per-label growth `log(1 + c/(2 − q))` (0.588 at `q = 1` against 0.351 at `q = 0.1` for `c = 0.8`). Nonzero anchors also update on unqueried events. |
| GRAPA, empirical Bernstein, plug-in (adaptive bets) | **Not covered** | Bets depend on history; GRAPA burns in on calendar events |
| Hard reserve stop | Validity is preserved (predictable stop); **allocation equivalence is not** | Different rules exhaust at different times |

**What L explains:** in label time, for HT with fixed-fraction stakes, evidence depends only on
which losses are labelled and in what order, not on the propensities. **It does not determine
calendar-time delay.** It is credited as elementary algebra on Timans et al.'s and Waudby-Smith et
al.'s betting framework. No novelty is claimed.

## 4. Formal setup, null and arm-by-arm validity

- **Filtration and feedback:** as in round 1, under the common-label contract.
- **Primary null:** `H_0: E[Z_t − ε | F_{t−1}] ≤ 0` for all `t` (charter).
- **Validity obligations by arm.** For each arm, the HT correction must be unbiased given
  `F_{t−1}` (query coin independent of `Y_t` given `F_{t−1}, X_t`; `D_t` observed). The bet and
  the normalising bound must be `F_{t−1}`-measurable, **or** a separate argument must cover bounds
  that depend on the current context.

| Arm family | `q_t` depends on | Bound depends on | Past-conditional validity |
|---|---|---|---|
| Fixed gating (`gated_ht_fixed`) | `D_t` (current) times a constant | constant | Holds: `E[V_t \| F_{t−1}] = E[Z_t − ε \| F_{t−1}]` because `Z_t = 0` when `D_t = 0` |
| Paced gating (`DisagreementPacer`, 200-event past window) | `D_t` times a past-window rate | past-window rate | Holds (bound is `F_{t−1}`-measurable) |
| Uniform PPI / HT | constant | constant | Holds |
| Xu active, PPE gated alias | per their source construction | per source | To be tabulated from `docs/xu_active_betting_paper_to_code_audit.md` and `ppe_paper_implementation_audit.md` (obligation) |

## 5. Matching levels and multiplicity families

**Matching levels:**
- **L1, common access:** same events, same information types.
- **L2, identical replay:** same streams, same query uniforms.
- **L3, common resource cap.**
- **L4, matched realized spend:** within a registered tolerance, or reported as a frontier.

S3 headline comparisons are L1–L3, with spend comparable but not matched. H4 arms are L1–L2 only;
they differ in action opportunities.

| Family | Error event | Correction |
|---|---|---|
| S2 null calibration | Any false alarm per arm across its scenario × budget cells | Simultaneous Bonferroni exact upper bound per arm |
| WP4 orientation nulls | False alarm per cell | Per-cell exact bounds. A conservative correction across all 68 cells still passes (about 0.72% upper bound; Codex). |
| S3 primary endpoints P1, P2 | Registered co-primary | As registered |
| E2 and E3 confirmatory endpoints | To be frozen | Holm within each registered family; TOST for equivalence claims |
| Operational monitor → certify → promote | **Not controlled; not claimed** | — |

## 6. Benchmark contract (the reusable deliverable)

A documented package other groups can use to evaluate a new monitor or controller:
- a task and feedback taxonomy (full, gated, paced, delayed; common-label versus action-dependent);
- evaluator-only oracle separation;
- baseline adapters with source-fidelity labels (HT/PPI, GRAPA, PPE, Xu, SR/CUSUM, Target-Scout,
  fixed certification, fallback, pipeline);
- immutable seed namespaces with a **machine-checked seed registry**, fixing the overlaps found in
  A2;
- resource accounting (labels, dollars, action opportunities);
- uncertainty procedures (exact intervals, McNemar, TOST, Holm);
- reference results with hashes.

Most components exist in `src/shiftlab/dive/`. The contract document and the registry are new
work.

## 7. Experiments (revised)

1. **E1. Reproduction, no new seeds.** An independent verifier recomputes H1–H4, the S2 and WP4
   tables, and Lemma L's exact identity on stored labelled-loss sequences where available. It also
   fixes the S2 seed-block typo and resolves the Target-Scout hash drift (run historical source or
   demonstrate equivalence).
2. **E2. Confirmation of findings 1 and 2, on a fresh registered seed block, CPU-sized first.**
   - *Arms:* gated HT, **uniform HT (same engine)** and uniform PPI. These separate acquisition
     from anchor and bound.
   - *Comparison:* fixed against paced gating, with onset swept independently of any stage
     boundary.
   - *Outputs:* deployed mixture log-wealth, detection and censored delay.
   - *Tests:* pre-registered paired tests (exact McNemar for detection; TOST for any equivalence
     claim) with power calculations.
   - *Mechanism:* fixed-window informative-label counts, predicting held-out cells.
3. **E3. Matched-opportunity intervention factorial, on a fresh registered seed block.**
   - *Factors:* response ∈ {revert, certify-and-promote} × latency ∈ {at alarm, at fixed stage}
     × rollback ∈ {on, off} × onset ∈ {before, at, after the stage boundaries}.
   - *Outputs:* an opportunity-loss decomposition. It tests whether response type, latency or
     rollback governs the rankings.
   - *Order:* smoke first; full run only after the protocol freeze.
4. **E4 (conditional on the user). A second task.** Post-freeze EIA as a prospective, locked
   evaluation window for the frozen WP4 bundle (the clock started 2026-10-27; the earliest useful
   check is around 2026-12-08). It needs the user to approve an EIA API key or a roughly 700 MB
   bulk pull. Without it, the real-data panel stays a retrospective stress test.

## 8. Success, failure and abandonment

- **Finding 1 confirmed** if, in E2, gated HT beats uniform HT and uniform PPI on paired detection
  (Holm-adjusted) at registered budgets.
- **Finding 2 confirmed** if fixed is non-inferior to paced (one-sided, registered margin) across
  the onset sweep.
- **Finding 3 resolved** if E3 identifies which factor or factors account for at least 50% of the
  utility differences. **Either answer is publishable for a benchmark:** response type matters, or
  only latency and rollback matter.
- **Lemma L** is checked exactly; any mismatch on stored sequences is an implementation finding.
- **Abandon the benchmark paper (decision NO_GO, technical report only)** if any of these holds:
  1. E1 fails on two or more of H1–H4.
  2. E2 fails to confirm both findings 1 and 2.
  3. A published matched-resource decision-harm benchmark covering findings 1–3 appears.
  4. The user declines both E3 compute and the benchmark-contract work, leaving only re-analysis
     of a single generator family.

## 9. Venue and expected strength

The target is **NeurIPS Datasets & Benchmarks or TMLR**. ICML main track is unlikely; Codex scored
it 3/10 before revision. **No new-method claim. The G4 / Paper 3 pre-screen stays separately gated
and is expected to stop** (tick-6 correction).

## Addendum (2026-10-28): E4 data-pull plan, approved for planning only

**User decision (2026-10-28):** plan the post-freeze EIA pull for around 2026-12-08. **Download
nothing until the user confirms the exact method and size.**

Both routes already exist in `src/shiftlab/data/real/eia.py`:

| Route | How | What it needs from the user | Expected size | Notes |
|---|---|---|---|---|
| **A. EIA API v2 (recommended)** | `acquire()` → `https://api.eia.gov/v2/electricity/rto/region-data/data/`, facets `respondent ∈ {CISO, ERCO}`, the WP4 series types, hourly, from 2026-10-19T18:00Z (snapshot end) to the pull date | A free EIA API key placed in the `EIA_API_KEY` environment variable **by the user**; the agent never handles the key | Small: about 2 respondents × a few series × ~1,200 hours. Estimated well under 5 MB as JSON. **To be measured with one metadata-only request (no data rows) before confirmation.** | Paged requests. Store raw JSON under ignored `data/raw/eia_api/` with a SHA-256 receipt. |
| B. Bulk snapshot | `_acquire_bulk()` → `https://www.eia.gov/opendata/bulk/EBA.zip` | Approval of a large download | About 700 MB (as for the previous snapshot) | Same extractor as the frozen bundle; heavier. |

**Protocol constraints for E4 (to freeze before any pull):**
- The evaluation window starts at the WP4 freeze, `2026-10-27T20:58:55Z`. Hours between the
  snapshot end (2026-10-19T18:00Z) and the freeze may only be used as feature warm-up.
- The frozen WP4 bundle (policies, tau, pacer, arms) is hash-checked against
  `docs/eia_real_data_validity_freeze.json`. The LF/CRLF re-hash issue must be resolved first.
- The 24-hour label delay is respected. Analyses (a)–(c) are as registered.
- About 1,000 hours per respondent is the earliest useful check.
- The result is the first **prospective** real-data evidence in the programme. It stays
  descriptive unless the protocol pre-registers a confirmatory endpoint.

## Addendum 2 (2026-10-28): use local data first; the E4 pull is deferred

**User direction (2026-10-28):** use the data already on disk (about 42 GB under `data/`) for
testing, rather than pull more. **The post-freeze pull above is deferred. It stays optional, as a
later prospective check, and still needs explicit confirmation of method and size.**

**Lead inventory (read-only):**
- The verified local snapshot `data/raw/eia/EBA.zip` (receipt present; 2019 to 2026-10-19)
  contains **70 hourly demand series** (`EBA.<BA>-ALL.D.H`).
- 14 of them are regional or national aggregates: CAL, CAR, CENT, FLA, MIDA, MIDW, NE, NW, NY, SE,
  SW, TEN, TEX, US48.
- That leaves **about 55 balancing authorities.**
- Only **CISO and ERCO** were used in any ShiftLab decision-harm or forecasting analysis.
- **NYIS** appears in 5 files: the loader default and early configs.
- PJM, MISO, ISNE, SWPP, SOCO, FPL, BPAT, TVA, DUK and the rest have **zero references** in docs,
  papers, configs or scripts.

**Revised E4: locked held-out balancing authorities from the existing snapshot (no download).**
1. **Outcome-free selection rule, frozen before any look at outcomes.**
   - Exclude the 14 aggregates and the examined authorities (CISO, ERCO, NYIS).
   - Keep the authorities whose demand series passes a coverage gate on demand availability alone
     (for example ≥ 95% observed hours in 2019–2024 and in the evaluation window).
   - Record the list and its hash.
2. **Split.**
   - With a pre-registered seed, assign about one third of the eligible authorities to a
     **development** set, used only for implementation checks and smoke runs.
   - Assign about two thirds to a **locked evaluation** set, which nobody opens until the
     protocol is frozen.
3. **Task.** The frozen WP4 paired reserve-procurement construction, unchanged:
   - tau = the 90th percentile of each authority's 2019–2024 demand;
   - shortfall and idle costs 5/1;
   - frozen Ridge against weekly-refit Ridge, with a 24-hour label delay;
   - a 2024 rehearsal for the pacer and the injection band.
   Analyses (a)–(c) as registered: the per-path orientation null, unmodified streams, and injected
   harm with known onset. The E2 arms (gated HT, uniform HT, uniform PPI; fixed against paced) are
   added under the same contract.
4. **What it adds.** Many new real paths for null validity and for the replication of findings 1
   and 2, on authorities never examined for this task.
5. **Limits, stated up front.**
   - The calendar period overlaps the examined CISO and ERCO windows. Authorities share weather,
     calendar and market shocks, so paths are correlated, not independent deployments. Use
     cluster-aware or per-path reporting.
   - Costs remain imposed, and publisher release timing is still unverified.
   - The result is **task-untouched retrospective** evidence, not prospective evidence.

**Other local sources considered:**

| Source | Size | Prior use | Fit to this proposal |
|---|---|---|---|
| OPSD (`data/raw/opsd`, 2020-10-06 snapshot; DE and DK hourly load, wind, solar, price, 2019) | 125 MB | Task report only (`docs/opsd_tasks.md`); no decision-harm run | **Secondary replication on a different grid**, under the same reserve construction, if its coverage passes. A short single year limits the rehearsal and evaluation split. |
| Folktables / ACS PUMS (2017–2019, by state) | 660 MB | Adapters only; no frozen task | **Offline cross-domain Q2 panel** (certify a candidate across state or year shift with an imposed cost matrix; the common label identifies both actions' costs). It is not sequential. Its use belongs to E3 or certification, not to monitoring. |
| Monash archive | 77 MB | Official-horizon diagnostics | Possible extra forecasting paths. Release times are unknown. Lower priority. |
| Open Bandit full (394 MB), Hillstrom | — | MOPE exploratory replay; exposed split | Action-dependent feedback (matrix G1). **Out of scope for Claim B.** |
| CriteoPrivateAds | 32 GB | One-seed delayed-feedback prediction replay | Prediction only, with no decision costs. Not needed. |
| CRSP (licensed) | 2.6 GB | Test window reused at least 5 times | Exposed; do not use for new claims. |

**Compute:** the WP4 build took about 85 s for 2 authorities (CUDA Ridge) and the vectorised replay
about 290 s on CPU. Roughly 35 locked authorities would take about an hour on CPU for the replay,
after a smoke run on the development set. That is CPU-sized, with no new data.
