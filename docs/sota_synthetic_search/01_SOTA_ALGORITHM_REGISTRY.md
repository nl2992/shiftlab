# SOTA algorithm registry

**Offline constraint.** `arxiv.org`, publisher and proceedings hosts are unreachable from the session shell; only abstract/snippet-level web search worked earlier (see `docs/rpoq_next/SOURCE_UPDATE.md` on the parent branch). No primary source was read in full in this phase. Therefore **no baseline below is a VERIFIED_REPRODUCTION**. Labels follow the brief; the "verification obligation" column records what a full reproduction would still need.

| ID | Method (source) | Implemented as | Provenance | Feedback contract | Threshold | Verification obligation |
|---|---|---|---|---|---|---|
| A1 | Windowed MMD, Gretton et al. 2012 | `detectors.mmd`: unbiased RBF MMD² between a fixed reference (first 200) and a sliding window, median-heuristic bandwidth | SOURCE_INSPIRED_BASELINE | unlabeled | empirical, null-calibrated max over horizon | permutation calibration; dependence-valid test |
| A2 | C2ST, Lopez-Paz and Oquab 2017 | `detectors.c2st`: LDA classifier, held-out t statistic | LOCAL_HEURISTIC | unlabeled | empirical | proper classifier two-sample test with accuracy null |
| A3 | BBSD / Failing Loudly, Rabanser et al. 2019 | `detectors.bbsd`: KS between reference and window model scores | SOURCE_INSPIRED_BASELINE | unlabeled (model outputs) | empirical | multi-dimensional representations, multiplicity |
| A4a | CUSUM | `detectors.cusum`, standardized labeled decision cost | SOURCE_INSPIRED_BASELINE | uniform labels, delay | empirical | none (classical) |
| A4b | Page–Hinkley | `detectors.page_hinkley` | SOURCE_INSPIRED_BASELINE | uniform labels, delay | empirical | none |
| A4c | ADWIN / two-window mean test | `detectors.twowin` | LOCAL_HEURISTIC | uniform labels, delay | empirical | exact ADWIN split search and bound |
| A4d | BOCPD | **not implemented in this phase** | — | — | — | open |
| A5 | Podkopaev–Ramdas risk monitoring, ICLR 2022 | `detectors.pr_cs`: labeled mean decision cost vs nominal risk with a stitched Hoeffding confidence sequence | SOURCE_INSPIRED_BASELINE | uniform labels, delay | theory (CS crossing) | their exact CS, source/target construction |
| A6 | WATCH, Prinster et al. ICML 2025 | `detectors.watch`: **unweighted** conformal test martingale on labeled `|y−p|` scores, mixture of power calibrators | SOURCE_INSPIRED_BASELINE (weights omitted) | uniform labels, delay | theory (1/α) | covariate-shift weights; their guarantees |
| A7 | PPRM, Zhang et al. ICML 2026 | `detectors.pprm`: prediction-powered Brier-risk increment + Kelly betting e-process | SOURCE_INSPIRED_BASELINE | uniform labels, delay | theory (1/α) | their exact CS and reliance-coefficient optimization |
| A8 | Prediction-Powered E-Values, Csillag et al. ICML 2025 | `detectors.pp_eprocess` (used by A7 and S01) | LOCAL_HEURISTIC (betting e-process on a PPI increment) | uniform labels, delay | theory (1/α) | the paper's factor-level construction |
| B1–B4 | Paired CS, Sequential Model Confidence Sets, CAMS | **Q2 not implemented in this phase** | — | — | — | open |
| C1–C4 | ASI, Robust ASI, PAI, Balanced AI | allocation rules planned for Q1 labeled monitors (S04–S06): uniform, Neyman-style, interpolation baseline | LOCAL_HEURISTIC / SOURCE_INSPIRED | — | — | estimator-side guarantees do not transfer to e-process power |
| C5 | Local hard-budget monitoring (RPOQ) | existing repo modules, not reused in this slice | — | — | — | — |
| C6 | Switching baselines | **Q3 not implemented in this phase** | — | — | — | open |
| ORACLE | Hindsight allocation / true-harm labels | evaluator-only | ORACLE_ONLY | — | — | never an implementable method |

**Scope of this phase.** Q1 (harmful-shift detection) with ten baselines implemented; Q2 and Q3 and candidates S07–S12 are listed as open work, not silently dropped.
