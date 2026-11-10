# User-supplied preliminary prior-art triage (2026-11-09)

Recorded verbatim in substance from the user's message. Status per the user: preliminary
source-backed triage, NOT a completed originality proof.

## Verdict
- NOT NOVEL AS GENERIC PROBLEMS: joint costly observation + actions; delayed sequential
  experimentation with adoption/switch; label timing under a strict query budget; learning
  hyperparameters across time-series tasks; drift alarms gating interventions;
  retrain/alert/rollback action sets; simple payback/hysteresis thresholds; generic POMDP planning.
- WORTH TARGETED INVESTIGATION: tractable two-law risk-envelope / pending-queue approximation with a
  new guarantee against a globally conditional null under adaptive acquisition; time-uniform future
  payback certificates under stated drift/persistence with resource-regret bounds; a new
  decision-harm/dependence benchmark with a causally isolated safe repair; cross-stream
  economic-policy transfer that controls negative transfer and beats calibrated non-neural/online
  meta algorithms on unseen domains.
- NOT YET CONFIRMED: novel algorithm, stronger SOTA, dependence robustness, >=2.5% gain,
  independent new real datasets.

## Source occupancy (URL -> covers -> hypothesised remaining gap, NOT proof)
| Source | URL | Covers | Hypothesised gap |
|---|---|---|---|
| Atan & van der Schaar 2016 | https://arxiv.org/abs/1602.03600 | joint costly observation + online decisions, sublinear regret | strict delay + global anytime causal-null risk + irreversible budget in a scalable rule |
| Chick, Forster & Pertile 2017 | https://doi.org/10.1111/rssb.12225 | sequential sampling, delayed response, adoption, costs | repeated rollback + robust conditional-null test under limited paired labels |
| Regol et al. ICML 2025 | https://proceedings.mlr.press/v267/regol25a.html | uncertainty-aware future retraining economics | proven forward economic certificate under nonstationary persistence, adaptive selection, delay |
| Cheng et al. ICML 2023 | https://proceedings.mlr.press/v202/cheng23f.html | observation budget + switching costs | delayed paired-label action risk contract and evidence routing |
| Drift2Act 2026 | https://arxiv.org/abs/2603.08578 | delayed labels, active current-risk certification, budgeted intervention | robust future economic switch value and/or provably more efficient joint policy |
| WISE-ATTA 2026 | https://arxiv.org/abs/2609.37687 | when to spend scarce supervision in TTA | not timing; only a distinct safety/economic intervention result |
| RAR Nov 2026 | https://arxiv.org/abs/2611.02251 | retrain/alert/rollback with costs | method/theorem advantage after source-faithful adaptation |
| Reyzin et al. UAI 2026 | https://proceedings.mlr.press/v337/reyzin26a.html | adaptive expert querying, heterogeneous fees | delayed intervention risk + full economic outcome |
| Goebel et al. AAAI 2026 | https://doi.org/10.1609/aaai.v40i45.41191 | finite-horizon scarce labels, episodic expert knowledge | risk-constrained reversible deployment |
| Gafni et al. ICML 2026 | https://proceedings.mlr.press/v306/gafni26a.html | multiple change points, regret lower bounds | joint delayed paid acquisition + economic action |
| Lopes et al. Sensors 2025 | https://doi.org/10.3390/s25092787 | meta-recommendation of CUSUM hyperparameters | economic, risk-controlled cross-domain policy transfer |
| Sow et al. 2024 | https://proceedings.mlr.press/v234/sow24a.html | task-boundary detection + online meta-learning | transferable paid-observation/deployment economics |
| Chen et al. IJCAI 2025 | https://ijcai.org/proceedings/2025/542 | meta-learning across concept drift | decision-controller transfer under scarce delayed labels |
| Liu et al. TPAMI 2026 | https://doi.org/10.1109/TPAMI.2026.3742576 | drift + delayed supervision with regret analysis | full economic intervention risk, query-side counterfactual value |

## Repository kill records that override enthusiasm
1. docs/g1_deadline_aligned_acquisition_kill_v1.md (deadline-aligned querying = POMDP VOI).
2. docs/switching_query_conditioned_deployment_extension_screen_v1.md.
3. docs/switching_action_matched_adaptive_acquisition_v1.md (gain over calendars = positive-prefix futility rule).
4. docs/switching_current_regime_evidence_v1.md (no future-value certificate after unrestricted reversal).
5. docs/switching_mechanism_screen_v1.md (bounded-drift age envelope already derived).
6. docs/failure_atlas_v2_report.md, docs/failure_atlas_v2_validation.md (RMM scoped; DISCERN fidelity).
7. research/multimodel-bcr-2026-11-08:docs/multimodel_bcr/09_FOLLOWUP.md (BCR negative vs K-Wald).
8. research/qsg-methods-search-2026-11-07:docs/qsg_methods_search/FINAL_PUBLICATION_DECISION.md.

## Kill tests per candidate
- A: write source-matched CPOMDP/active-observation formulations; prove not a reparameterisation;
  compare to small exact risk-constrained oracle and a strong MPC/risk-gated planner.
- B: theorem beyond the internal age-corrected Hoeffding bound; audit time-uniform validity and
  adaptive stopping; compare budget/power/delay with sequential experimentation, confidence
  sequences, known-model Bayes planning.
- C: previously unreported causally isolated mechanism; multiple source-faithful methods with sound
  null validity; external relevance; new protocol or attributable repair.
- D: leave-family-out vs direct meta-recommendation, hierarchical pooling, expert tracking,
  per-domain tuning at identical supervision cost; show negative transfer; ideally a risk-preserving
  transfer bound.

Novelty labels to use: covered / conditional / unverified / supported.
