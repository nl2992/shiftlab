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
| Companion method | Optional | FLQ / budget-feasible front-loaded pacing is a simple repair suggested by the diagnosis | Re-registered run on fresh seeds under the two-tier criterion. Present it as a baseline the findings motivate, not a new algorithm |

## 3. Introduction logic chain

| Part | Content |
|---|---|
| 1. Background + running example | A team has an incumbent and a challenger forecaster, 200 labels for 2,000 predictions, and labels that arrive late. An anytime-valid certificate decides when to swap. **Running example (Fig. 1):** on a ρ=.8 Markov null, front-loading a gated certificate raises promotions from 0 to .16, so a single-null gate calls it uncertified. Its paired cost vs the host on that null is −0.5 [−2.5, +1.8]. The validity verdict and the economic verdict disagree (`failure_atlas_v2_flq/results/validation_synthetic.md`) |
| 2. Limitations (3) | L1: methods are validated on synthetic iid or the authors' own null, never on a known null built from real data. L2: evaluations score validity or cost, not both under the same budget and delay. L3: comparisons leave the label-acquisition layer unspecified, which confounds certificate design with pacing |
| 3. Research questions | RQ1: does certificate validity survive realistic dependence, and against which null? RQ2: when validity "fails", is the promotion economically harmful? RQ3: what drives cost differences among certified methods: certificate, acquisition, or horizon and delay? |
| 4. Design considerations | Exact known nulls on real data; matched information (budget, delay, propensities); every method scored on every null with its claimed null labelled; source-cluster uncertainty; untouched confirmation sources; executable common contract |
| 5. Proposal | The benchmark: twin nulls, dependence classes, alternatives, ≥ 20 methods, the three-null matrix with all-in cost, and the pacing-matched evaluation protocol. Optionally, FLQ as a diagnosis-driven baseline |
| 6. Contributions | (1) Benchmark and construction pipeline with exact real-data nulls. (2) Two-tier evaluation protocol: claimed-null validity plus dependent-null economics. (3) Systematic evaluation of certified, uncertified and control policies. (4) Findings 1–5, including the pacing confound |

## 4. Findings already in hand (development, exposed data)

| # | Finding (draft) | Evidence | Status |
|---|---|---|---|
| F1 | V1 certified methods break the marginal null on real twins; the rate grows with horizon | Pooled V1-certified promotion on v2 twins .141 [.120, .163]. Pooled rate .112 → .156 → .187 for T = 1000/2000/4000 (delay ×1) (`amended_no_xu_pool/results.json`, H2/H6a). Strict 6-port sensitivity: H1a false (4/6 vs threshold 5) | Replicated across sprint 1 and v2 splits; sensitive to comparator pool |
| F2 | Those promotions are conditionally informed | Mean remaining advantage at promotion .0122 [.0063, .018] (H2 pass) | Development |
| F3 | Neither null tracks economic appropriateness | About half of first promotions are EI under both persistence classes: mean-reverting .49 [.42, .56], fixed-effect real .49 [.44, .54], fixed-effect synthetic .44 [.36, .53] (H4 registered rule fails) | Development; EI is a hold-to-end proxy that excludes label cost |
| F4 | Uncertified selectors fail badly on nulls | bike_hour twins: CAMS adapter promotes .908, ModelPicker .875, with excess cost 10.7 and 8.4 vs −0.9 to 5.6 for certified and internal rows. Atlas v2 V_null: uncertified rows .63–.99 | Development |
| F5 | Robustness to dependence costs a lot | A5b − QSG on real realised-better episodes: ΔJ +118.5 [+89.3, +150.1], first promotion +972 events later (H5) | Development; conditions on realised advantage (descriptive) |
| F6 | Pacing, not the certificate, explains most certified-method cost gaps | Front-loaded vs unmodified gated: −24.55 [−42.81, −6.29] over 14 source clusters; front vs tuned pace −0.30 [−1.05, +0.45]; front vs C2 +0.60, vs C6 +0.03 (corrected replay, **unmerged** branch `codex/scoped-method-research-results-2026-11-06`) | Exposed, constructed streams; imposed delays |
| F7 | Even a marginal-null method fails on one real dataset | A5b's upper bound on bike_hour .192 > .0936 (H1b fails) | Needs ≥ 60 splits to separate design noise from real failure |

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
| W1 | Merge the corrected-port (wmaxfix) replays and fix the test environment. In this worktree `.venv` lacks pytest and `uv run` collects 93 errors (missing torch); a combined run has a `regimes` import collision | The benchmark must use corrected ports; the suite must run green | Small |
| W2 | Verified literature search and related-work table | The gap is the contribution; an unverified gap is fatal | Medium |
| W3 | Comparator fidelity: per port, reproduce one published result or check against author code where it exists | "Ports, not author-native" is the first reviewer objection | Medium–large |
| W4 | Freeze the two-tier criterion and register F1–F7 as hypotheses with power analysis (≥ 60 twin splits per dataset; C7 in the criteria review) | Turns development findings into confirmatory ones | Small to register; medium compute |
| W5 | Add 2–4 untouched chronological sources with imposed, swept delays: candidates are Wild-Time HuffPost/arXiv from raw records, UCI Online Retail II, and OPSD as the external-clock case study | Generality beyond 5 UCI-derived datasets that are already exposed | Large (acquisition, license, checksums, one-shot runner) |
| W6 | Fresh-seed confirmatory run, then a single opening of the untouched sources | Confirmation | Medium compute |
| W7 | Release package: one-command runner, data card, licenses, maintenance plan | Benchmark acceptance norms | Medium |
| W8 | Figures. PaperBanana is not available in this environment (required by AGENTS.md) | Fig. 1, Fig. 2 and the result plots | Blocked on the dependency |
| W9 | External review of the claims | Recorded as open in the Sprint 2 exit audit | Depends on people |

## 7. Pre-submission checklist: unresolved items

**Critical (4):** no verified benchmark comparison table (W2); no pipeline figure or running-example
figure (W8); no confirmatory evidence, only development runs (W4–W6); no released, runnable package,
and the test suite does not currently run in this worktree (W1, W7).

**Major (6):** method coverage is ~25 policies but none are author-native (W3); real data is 5
exposed UCI-derived sources (W5); the bike_hour twin result is underpowered (W4); the decision-harm
framing must be cut back to prediction-loss economics everywhere; no data card or maintenance plan
(W7); EI is a proxy that excludes label cost (report all-in cost as primary).

Not applicable: a human baseline (no human decision makers are in the loop).

## 8. Decisions needed

1. Adopt the two-tier validity criterion (claimed-null gate + dependent-null economics) as the
   benchmark's protocol and the programme's acceptance rule?
2. Accept imposed, swept delays on untouched chronological sources as the real-data standard, with
   OPSD as the only external-clock case study?
3. Include FLQ as a companion baseline (requires one re-registered fresh-seed run), or keep the paper
   as evaluation only?
4. Target venue and deadline, to be confirmed. Scope W1–W4 first either way; W5 is the long pole.
