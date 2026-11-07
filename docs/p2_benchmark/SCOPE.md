# P2 benchmark paper: scope (2026-11-06)

**Status:** scoping document, not a result. All numbers quoted below are development evidence on
previously exposed data, cited to their source files. Ports are common-contract re-implementations,
not author-native code. The companion review of acceptance criteria is
[ACCEPTANCE_CRITERIA_REVIEW.md](ACCEPTANCE_CRITERIA_REVIEW.md).

## 1. Thesis

Certified challenger-promotion methods are judged against the null each one assumes. Real deployment
streams are temporally dependent, and on them that null-relative validity diverges from economic
value:

- conditional-null (V1) certificates promote well above α on exact known marginal nulls built from
  real data;
- those promotions are conditionally informed, so they are not simply errors;
- neither the conditional nor the marginal null tracks whether a promotion pays for itself;
- among certified methods, label pacing drives cost more than the choice of certificate.

The benchmark makes these trade-offs measurable on one common contract: a hard label budget, delayed
labels, switch cost, a three-null violation matrix, and all-in economic cost.

**Working title:** *Which Null Should Certify a Model Swap? A Dependence-Aware Benchmark for
Label-Budgeted Deployment Decisions.*

**Scope boundary:** prediction-loss and switching economics between an incumbent and a challenger
model. Application-level decision harm is **out of scope**, because no dataset supplies causal
utilities. No new theorem and no universal SOTA claim.

## 2. Five-pillar audit

| Pillar | Covered? | What exists | What is missing |
|---|---|---|---|
| Research gap | Partly | Conditional vs marginal predictive ability is classical (Giacomini–White 2006; Diebold–Mariano). The anytime-valid versions exist (Henzi–Ziegel 2022; Choe–Ramdas 2024). The gap is evaluation: no shared contract scores deployment certificates under budget, delay *and* dependence against their claimed null *and* economic outcome | A verified related-work table of ≥ 5 benchmarks/evaluations (shift benchmarks such as WILDS and Wild-Time; sequential-testing evaluations). **No literature search has been verified for this framing yet** |
| Construction pipeline | Yes, undocumented as a pipeline | Exchangeable-twin known nulls (`twin_null.py`; 5 datasets × 40 splits, hash-reproduced 5/5), synthetic dependence classes (`fam_f.py`, `ooc_regimes`), fresh-real alternatives, common simulator with frozen propensities and delayed release | A formal statement of why twin marginal advantage = 0; generator validation for each dependence class; a pipeline figure; a dataset statistics table; untouched sources |
| Evaluation framework | Yes | Three-null matrix (V1 at H=100/500, V2, V3 EI proxy), path harm, all-in excess cost decomposed into loss, labels and switches; cluster bootstrap at source/split level (`sprint2/wp2/BENCHMARK.md`) | A primary-metric hierarchy for the paper; per-regime difficulty tiers; Pareto views of validity vs cost |
| Empirical findings | Yes, development-stage | See section 4 | Confirmation on fresh seeds and untouched sources; corrected (wmaxfix) ports throughout |
| Companion method | Not warranted | The registered FLQ re-test (2026-11-06) was NOT_SUPPORTED on efficacy: 2/6 new instances, blocked by SMCS and the Xu composite | Keep the paper evaluation-only. Use the re-test as evidence that the gate choice reorders the leaderboard |

## 3. Introduction logic chain

| Part | Content |
|---|---|
| 1. Background + running example | A team has an incumbent and a challenger forecaster, 200 labels for 2,000 predictions, and labels that arrive late. An anytime-valid certificate decides when to swap. **Running example (Fig. 1):** on a ρ=.8 Markov null, front-loading a gated certificate raises promotions from 0 to .16, so a single-null gate calls it uncertified. Its paired cost vs the host on that null is −0.5 [−2.5, +1.8]. The validity verdict and the economic verdict disagree (`failure_atlas_v2_flq/results/validation_synthetic.md`) |
| 2. Limitations (3) | L1: methods are validated on synthetic iid or the authors' own null, never on a known null built from real data. L2: evaluations score validity or cost, not both under the same budget and delay. L3: comparisons leave the label-acquisition layer unspecified, which confounds certificate design with pacing |
| 3. Research questions | RQ1: does certificate validity survive realistic dependence, and against which null? RQ2: when validity "fails", is the promotion economically harmful? RQ3: what drives cost differences among certified methods: certificate, acquisition, or horizon and delay? |
| 4. Design considerations | Exact known nulls on real data; matched information (budget, delay, propensities); every method scored on every null with its claimed null labelled; source-cluster uncertainty; untouched confirmation sources; executable common contract |
| 5. Proposal | The benchmark: twin nulls, dependence classes, alternatives, ≥ 20 methods, the three-null matrix with all-in cost, and the pacing-matched evaluation protocol. Optionally, FLQ as a diagnosis-driven baseline |
| 6. Contributions | (1) Benchmark and construction pipeline with exact real-data nulls. (2) Two-tier evaluation protocol: claimed-null validity plus dependent-null economics. (3) Systematic evaluation of certified, uncertified and control policies. (4) Findings 1–5, including the pacing confound |

## 4. Findings (development evidence; W4 confirmatory status per row, exposed sources)

| # | Finding (draft) | Evidence | Status |
|---|---|---|---|
| F1 | V1 certified methods break the marginal null on real twins; the rate grows with horizon | Pooled V1-certified promotion on v2 twins .141 [.120, .163]. Pooled rate .112 → .156 → .187 for T = 1000/2000/4000 (delay ×1) (`amended_no_xu_pool/results.json`, H2/H6a). Strict 6-port sensitivity: H1a false (4/6 vs threshold 5) | **Confirmed on twin v3 (H1):** strict pool .098 [.091, .106] (99%); T = 1000/2000/4000 → .073/.098/.104 ([confirmatory](results/CONFIRMATORY_RESULTS.md)) |
| F2 | Those promotions are conditionally informed | Mean remaining advantage at promotion .0122 [.0063, .018] (H2 pass) | **Confirmed (H2):** .0152 [.0114, .0198] ([confirmatory](results/CONFIRMATORY_RESULTS.md)) |
| F3 | Neither null tracks economic appropriateness | About half of first promotions are EI under both persistence classes: mean-reverting .49 [.42, .56], fixed-effect real .49 [.44, .54], fixed-effect synthetic .44 [.36, .53] (H4 registered rule fails) | **Equivalence passes (H3):** .530 vs .444, difference [+.032, +.141] inside ±.15 but excludes 0 ([confirmatory](results/CONFIRMATORY_RESULTS.md)). EI excludes label cost |
| F4 | Uncertified selectors fail badly on nulls | bike_hour twins: CAMS adapter promotes .908, ModelPicker .875, with excess cost 10.7 and 8.4 vs −0.9 to 5.6 for certified and internal rows. Atlas v2 V_null: uncertified rows .63–.99 | **Confirmed (H4):** per-dataset 99% LB .66–.92 ([confirmatory](results/CONFIRMATORY_RESULTS.md)) |
| F5 | Robustness to dependence costs a lot | A5b − QSG on real realised-better episodes: ΔJ +118.5 [+89.3, +150.1], first promotion +972 events later (H5) | **Confirmed on synthetic dependent alternatives (H5):** +50.3 [+47.0, +53.5] ([confirmatory](results/CONFIRMATORY_RESULTS.md)) |
| F6 | Pacing, not the certificate, explains most certified-method cost gaps | Front-loaded vs unmodified gated: −24.55 [−42.81, −6.29] over 14 source clusters; front vs tuned pace −0.30 [−1.05, +0.45]; front vs C2 +0.60, vs C6 +0.03 (corrected replay, **unmerged** branch `codex/scoped-method-research-results-2026-11-06`) | Exposed, constructed streams; imposed delays |
| F8 | The validity gate reorders the leaderboard | Registered re-test: front-loading passes the two-tier rule, with dependent-null cost ≤ its host's despite 2–4× more promotions. Re-admitting SMCS under the same rule blocks front-loading's wins ([results](results/FLQ_TWO_TIER_RESULTS.md)) | Fresh seeds, synthetic. **H7 (twin v3 / fresh real):** the all-null gate admits only `discern_style`, the costliest; the Tier A-only gate admits all 16, so restate F8 as "all-null gate is degenerate" until a Tier B gate is registered ([confirmatory](results/CONFIRMATORY_RESULTS.md)) |
| F7 | Even a marginal-null method fails on one real dataset | A5b's upper bound on bike_hour .192 > .0936 (H1b fails) | **Confirmed (H6b, 120 splits):** bike_hour .089, 99% LB .067 > .05, 95% UB .105; other four datasets meet .0936 ([confirmatory](results/CONFIRMATORY_RESULTS.md)) |

## 5. Section skeleton

- **§2 Task and design goals.** Promotion problem, filtration, budget and delay contract, the three
  nulls and the objective J. Goals: G1 exact real-data nulls, G2 matched information, G3 null-labelled
  scoring, G4 reproducibility and untouched confirmation. *Table: the null each method claims.*
- **§3 Construction pipeline.** Twin construction (with the marginal-zero argument), dependence
  classes, alternatives, delay grid, untouched sources. *Fig. 2: pipeline. Table 2: stream
  statistics, including estimated ρ per dataset.*
- **§4 Companion baseline (optional).** Budget-feasible front-loaded pacing; its region and its
  reversal cost.
- **§5 Experiments by RQ.** *Table 3: the three-null matrix for all methods on all streams.* RQ1:
  validity vs dependence and horizon. RQ2: economics of "invalid" promotions. RQ3: decomposition into
  certificate, acquisition and horizon/delay, including a pacing-matched re-ranking. Bold *Finding X*
  after each.
- **§6 Discussion.** When to prefer V1, V2 or V3 gates; recommendations for authors of new
  certificates; limits (no causal utility, imposed delays).
- **§7 Related work.** *Table 1: benchmark comparison* (needs a verified search).

## 6. Work plan (ordered by risk)

| # | Item | Why it is needed | Size |
|---|---|---|---|
| W1 | **Done 2026-11-06.** Corrected ports merged (fast-forward to `c0a5017d`, plus the MOPE intersection fix `0c52913c`); full suite green, 3,337 passed ([ENVIRONMENT.md](ENVIRONMENT.md)) | The benchmark must use corrected ports; the suite must run green | Done |
| W2 | **First pass done.** [RELATED_WORK.md](RELATED_WORK.md): closest prior work is arXiv 2609.04388, so the gap statement must narrow. Re-check later sections and new preprints before submission | The gap is the contribution; an unverified gap is fatal | Re-check before submission |
| W3 | **Done 2026-11-07.** [COMPARATOR_FIDELITY.md](COMPARATOR_FIDELITY.md). Exact parity for SMCS, CAMS and Model Picker; gated bets match MOPE author code, endpoints conservative (~1.5× wider); Choe–Ramdas stand-in more aggressive than `comparecast`; no DISCERN code exists | "Ports, not author-native" is the first reviewer objection | Optional: exact-grid gated endpoint |
| W4 | **Done 2026-11-07.** [CONFIRMATORY_HYPOTHESES.md](CONFIRMATORY_HYPOTHESES.md), [confirmatory](results/CONFIRMATORY_RESULTS.md): H1, H2, H4, H5, H6b pass; H3 equivalence passes; H7 top changes but the Tier A-only gate does not discriminate | Turns development findings into confirmatory ones | Done |
| W5 | Add 2–4 untouched chronological sources with imposed, swept delays: candidates are Wild-Time HuffPost/arXiv from raw records, UCI Online Retail II, and OPSD as the external-clock case study | Generality beyond 5 UCI-derived datasets that are already exposed | Large (acquisition, license, checksums, one-shot runner) |
| W6 | Fresh-seed confirmatory run, then a single opening of the untouched sources | Confirmation | Medium compute |
| W7 | Release package: one-command runner, data card, licenses, maintenance plan | Benchmark acceptance norms | Medium |
| W8 | Figures. PaperBanana is not available in this environment (required by AGENTS.md) | Fig. 1, Fig. 2 and the result plots | Blocked on the dependency |
| W9 | External review of the claims | Recorded as open in the Sprint 2 exit audit | Depends on people |

## 7. Pre-submission checklist: unresolved items

**Critical (3, updated 2026-11-07):** no pipeline figure or running-example figure (W8); confirmatory
evidence exists only on exposed sources (W4 done; untouched-source confirmation W5–W6 open); no
released, runnable package (W7). Resolved: a verified first-pass comparison table exists (W2), and the test suite is green (W1).

**Major (6):** method coverage is ~25 policies, ports only, with author parity for SMCS, CAMS, Model Picker and gated bets (W3); real data is 5
exposed UCI-derived sources (W5); F8 needs a registered Tier B gate before the reordering claim stands; the decision-harm
framing must be cut back to prediction-loss economics everywhere; no data card or maintenance plan
(W7); EI is a proxy that excludes label cost (report all-in cost as primary).

Not applicable: a human baseline (no human decision makers are in the loop).

## 8. Decisions needed

1. Adopt the two-tier validity criterion (claimed-null gate + dependent-null economics) as the
   benchmark's protocol and the programme's acceptance rule?
2. Accept imposed, swept delays on untouched chronological sources as the real-data standard, with
   OPSD as the only external-clock case study?
3. Settled: FLQ is not a companion method (registered re-test NOT_SUPPORTED). The paper is evaluation-only.
4. Target venue and deadline, to be confirmed. Scope W1–W4 first either way; W5 is the long pole.
