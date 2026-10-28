# Codex Stage 1 protocol review (round 2)

Reviewer: Codex CLI `codex exec --sandbox read-only`, `model_reasoning_effort=xhigh`, 2026-10-28, HEAD `6fac87c`. Verbatim final answer below. Verdict: all four DO-NOT-FREEZE with minimal blockers.

**None is ready to freeze unchanged.** Reviewed clean HEAD `6fac87c`. No files edited; no `data/` or raw data read. Tests inspected, not rerun: the available Python executable was denied execution.

**P1 / E2 — DO-NOT-FREEZE**

- **RESOLVED — round-1 FATAL:** non-ceiling development selection, exhaustion bands and the horizon baseline are implemented. The grid manifest identifies `e2_dev_grid`; seven tests, cells, order and sample sizes are locked before confirmation. [manifest:4](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/e2_grid/manifest.json:4), [locked design:29](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P1_E2_locked_design.json:29).
- **RESOLVED — round-1 MAJOR:** H-B1 is explicitly a gating ablation; H-B1b measures acquisition expenditure and requires detection non-inferiority. [protocol:172](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P1_E2_protocol.md:172).
- **RESOLVED — freeze gate:** hashes and cleanliness are checked before confirmation seeds are generated. [runner:93](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e2_acquisition_pacing.py:93), [freeze.py:59](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/freeze.py:59).
- **PARTIAL — grid completeness:** validation checks consistency between seeds, not the required arm/engine set; removing an entire secondary arm from every seed passes. [analysis:51](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/analyze_e2.py:51).

**Additional blocker found, pre-existing rather than revision-introduced:** NI inversion searches through `alpha=0.999`, beyond the lower-bound formula’s monotone branch. Counts `(1100,420,480,1000)` give lower bound `−0.04684` at `0.025/7`, yet return `p=1` because the `0.999` check gives `−0.05088`. [analysis:112](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/analyze_e2.py:112).

**Minimal changes:** repair and regression-test NI inversion; recheck development power on the same selected cells; validate complete arm/engine sets. The reported **0.86–0.90 power is a qualified simulation estimate**, not an established 90% floor, and must be reassessed after that repair. [protocol:240](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P1_E2_protocol.md:240).

**P2 / E3 — DO-NOT-FREEZE**

- **RESOLVED — round-1 FATAL:** seven-dose operating-region analysis, continue/matched-wait controls and unconditional utility replace selected-point replication. Development metadata confirms seeds **100200200–599**; confirmation starts at **100300000**. [dev manifest:5](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/e3/dev_v2_n400/manifest.json:5), [protocol:80](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P2_E3_protocol.md:80).
- **RESOLVED — round-1 MAJOR:** certificate scope is accurately narrowed; failure to locate crossover no longer establishes a named mechanism. The decomposition is correct: `U(promote)−U(revert)=−U(revert)+U(promote)`, because continue has zero utility. [protocol:20](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P2_E3_protocol.md:20), [analysis:174](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/analyze_e3.py:174).
- **PARTIAL — freeze/completeness:** listed-file hashing and per-seed factorial checks work, but confirmation accepts arbitrary `n`, and analysis accepts omission of whole seeds. [runner:117](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e3_intervention_factorial.py:117), [analysis:69](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/analyze_e3.py:69).

**NEW blockers:** the crossover bracket uses the immediately preceding dose even when its sign is unresolved; use the last certified revert-side dose, or report only the first significant grid dose. Also, an inconclusive promotion-component band does not establish “abstention-only.” [analysis:132](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/analyze_e3.py:132), [protocol:90](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P2_E3_protocol.md:90).

**Minimal changes:** fix bracket/claim wording; enforce `n=1000` and exactly seeds `100300000–100300999` in runner and analysis.

**P3 / E4 — DO-NOT-FREEZE**

- **RESOLVED — round-1 FATAL:** locked mode, atomic one-opening marker before reading, and freezing the new runtime composition are implemented. [runner:648](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e4_heldout.py:648), [runner:673](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e4_heldout.py:673).
- **RESOLVED — round-1 MAJOR, replication:** fixed 1,000 replicates, no rerun selection, Bonferroni over paths × 17, and insufficient-validation wording replace the mismatched procedure. [runner:218](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e4_heldout.py:218), [runner:247](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e4_heldout.py:247).
- **PARTIAL — round-1 MAJOR, informativeness:** arm/budget screens and exclusion of structural `q=1` transfer support are added, but the information calculation ignores reserve stopping. [runner:200](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e4_heldout.py:200), [runner:369](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/run_e4_heldout.py:369).

**NEW blocker:** full-path `ΣDq` can count disagreements occurring after reserve exhaustion, falsely qualifying an uninformative path.

**Minimal changes:** calculate information over processed prefixes and test exhaustion-before-disagreement; complete the protocol’s explicit region-map verification precondition. [protocol:377](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P3_E4_protocol.md:377).

**P4 / benchmark gate — DO-NOT-FREEZE**

- **PARTIAL — round-1 FATAL:** subprocess/JSON separation protects parent state, but `python -I` and changing directories leave evaluator files accessible through absolute paths. A packet-only implementer session does not remove runtime filesystem access. [sandbox.py:13](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/contract/sandbox.py:13), [sandbox.py:171](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/contract/sandbox.py:171).
- **RESOLVED — round-1 MAJOR, scientific fidelity:** numerical fixtures, explicit HT/null/bound arguments and WATCH’s exclusion as the primary method are required. [protocol:96](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P4_benchmark_value_gate.md:96).
- **RESOLVED — round-1 MAJOR, bounds:** global/predictable bounds versus a stronger context-conditional null are distinguished correctly. [README:49](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/CONTRACT_README.md:49).

**No additional revision-introduced blocker.** **F=0.25 is explicitly registered**, and rules out an always-zero statistic. [protocol:141](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/research_refinement_v1/stage1/P4_benchmark_value_gate.md:141).

**Minimal change:** execute the adapter where evaluator files are absent or inaccessible; test absolute-path access denial. The current relative-path test demonstrates a missing file, not filesystem isolation. [test:111](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/tests/test_contract_sandbox.py:111).
