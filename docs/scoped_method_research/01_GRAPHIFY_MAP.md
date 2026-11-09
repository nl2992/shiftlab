# Graphify repository map

Generated with Graphify v0.9.103 on 2026-11-06 in the isolated research worktree at
`c66185c0a1f3338e7422cfceeeedd0694867fb74`. Scope: relevant research areas (simulator, adaptation,
certification, baselines, experiment protocols, data and tests), not the entire repository. The build
reports 389 files / 423,444 words, 5,828 nodes, 15,768 edges and 249 communities. Its structural
diagnostic reported no missing/dangling edges, exact duplicate files, or directed endpoint collapse;
12 possible producer-side suppressions cannot be determined from the completed graph alone.

The graph was queried for the simulator, baselines, acquisition modules, statistical guarantees,
deployment rules, prior audits, datasets, test coverage and experiment dependencies. Graph results
were treated as navigation, then checked against source because extracted relation details can be
noisy (the `_rb()` result, for example, resolved only to a factory call).

| Question | Graph path / source checked | Verified interpretation |
|---|---|---|
| What does one round expose? | `simulator.py` → event loop; source `src/shiftlab/simulator.py` | Pending labels release at round start; policy sees only released/query-observed outcomes before acting. Predictions/losses occur before queries; requested labels are charged then and released at `t+delay`. With delay ≥1 there is no same-round feedback. |
| Where are rollback policies? | `fam_e.py` → `fam_b.py::RecoveryMonitor` | E_rb wraps the Family B recovery monitor; inspect factories and wrapper parameters in source, not the graph's inferred `_rb()` edge. |
| What is the E_rb guarantee? | `fam_e.py::E_rb` → recovery detector | Restart-mixture recovery statistic with alpha allocation and horizon gate. Its guarantee is conditional on the stated iid/conditional null and filtration assumptions; the implementation name is not itself a validity proof. |
| What do other restart detectors guarantee? | `fam_e.py::E_srr`, `SRRDetector`, `DetectorSwapMonitor` | Start-at-every-label SRR/CUSUM has an ARL interpretation, not E_rb's anytime family-wise bound; GLR likewise is not certified by that wrapper. |
| What acquisition controls exist? | `fam_c.py` C2/C6; `fam_b.py` reserve; `fam_e.py` no-acquisition variants | Existing throttling, deadline, reserve and continued-acquisition variants make simple compositions prior implementations rather than new methods. |
| What tests cover these paths? | `tests/sota_sprint/test_fam_b.py`, related `test_fam_*.py` | Tests cover reserve/rollback/deadline/null behavior; see audit artifact for isolated test commands/results. Unit tests do not establish statistical validity. |
| Which evidence is exposed? | Sprint 2 WP1/WP2 ledgers and Failure Atlas reports | Corrected replay summaries are development/exposed evidence; no fresh real-source confirmation is established. |

The complete query transcripts and graph build outputs are retained under the worktree's
`graphify-out/` and `.codex/` directories. The build is a navigation aid, not a scientific result.
