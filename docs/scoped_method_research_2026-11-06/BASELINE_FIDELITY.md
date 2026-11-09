# Baseline fidelity and novelty audit

| Method family | Repository implementation | Correct scope / caveat | Relevant evidence |
|---|---|---|---|
| Xu | Xu-inspired acquisition adapter + ShiftLab certificate | Acquisition-only adapter; not the published Xu certificate | `docs/sprint2/SOTA_BENCHMARK_AUDIT.md`; `scripts/sota_sprint/bench2.py` |
| DISCERN-style | Formula/paired-loss port | Corrected variance scaling is documented; not author-native parity | `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md`; `scripts/promising_directions/sota/competitors/certificate_stops.py` |
| Gated / adaptive range | Common-contract deployment port | Predictable range ordering bug corrected; replay coverage remains incomplete in Sprint 2 | `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md`; `docs/sprint2/EXIT_AUDIT.md` |
| E_srr / SRR | Restart e-detector and acquisition variants | Report ARL where that is the calibration; do not recast as a horizon-wise FWER certificate | `scripts/sota_sprint/fam_e.py`; `docs/sprint2/wp1/RESULTS.md` |
| E_rb | Certified rollback wrapper | Existing implementation; alpha and start grid are material; horizon gate was non-binding in reported ablation | `scripts/sota_sprint/fam_e.py`; WP1 results |
| RMM | Restart mixture monitor | Not significantly better than E_srr on the retrospective real late stratum | WP1 results and `docs/sprint2/novelty/NOVELTY.md` |
| Gated front-loaded | Adaptive-range Gated host plus front-loaded acquisition schedule | Stronger acquisition comparator; corrected replay required for affected same-seed entries | `docs/failure_atlas_v2_flq/results/validation_synthetic.md`; `scripts/failure_atlas_v2_flq/strong_hosts.py` |
| Fast selectors (e.g. CAMS / selector ports) | Operational selection adapters | Compare net cost and their own validity target; faster selection is not itself a failed certificate | `docs/sprint2/SOTA_BENCHMARK_AUDIT.md`; `docs/sprint2/wp2/BENCHMARK.md` |

## Target and fidelity registry

| Comparator | Target it can speak to | Code origin / information | Role in a valid matched study |
|---|---|---|---|
| Corrected Gated / Gated+front | Registered first-promotion certificate under stated assumptions; economic cost separately empirical | ShiftLab common-contract port with adaptive acquisition | Corrected certificate comparator for late promotion; preserve null checks and replay status |
| DISCERN-style corrected | Confidence-sequence target under assumptions; common-contract cost | Formula port with corrected scaling, not author-native deployment parity | Certificate comparator; stale pre-correction values excluded |
| SMCS | Its own sequential deployment rule and target | Implemented common-contract policy | Certificate/operational comparator with explicit target |
| RMM | Restart-mixture conditional evidence target under assumptions; cost separately empirical | ShiftLab wrapper over certificate host | Existing candidate baseline, not novelty evidence |
| E_srr | ARL-to-false-alarm target for cited restart process | Python reimplementation plus matched acquisition wrapper | Restart comparator; ARL does not imply P(any false alarm) control |
| E_rb | Existing rollback wrapper's stated conditional error accounting; cost empirical | ShiftLab recovery monitor | Reversal comparator and attribution target; not a new published method |
| Xu acquisition-only | No published certificate claim in this paired construction | Xu acquisition component plus ShiftLab host certificate | Acquisition ablation only; not Xu's full paper algorithm |
| CAMS / fast selectors | Method-specific selection or operational target | Common-contract adapters with documented protocol differences | Report native target and net-cost frontier; do not call no-certificate selectors theorem failures |

All methods require the same horizon, pathwise query cap, label release stream, query price, switch price and permitted information. Policy-visible feedback is limited to released queried labels and pending metadata; evaluator truth remains outside the policy. Cost comparisons are meaningful only when this shared contract is implemented and source-method deviations are disclosed.

## Novelty determination

The proposed reserve-aware restart mixture combines established restart detection, sequential testing, disagreement sampling, and budget-aware acquisition ingredients. Existing evidence does not show an incremental benefit beyond matched SRR and continued acquisition. A cost-aware mirrored rollback/hysteresis rule likewise overlaps with two-sided/repeated change detection and E_rb. The WP1 ablation states the horizon gate never binds and that the rollback alpha/start-grid explains the observed synthetic gain. Therefore neither is presently a defensible novelty claim.

The corrected Sprint 2 replay adds a narrow economic result for existing C2/C6: each reduces mean J by about 7.4–7.8 versus Gated+front in two synthetic late alternatives, while promotion remains at or below 1%. This effect is not explained by front-loading alone within those cells, but it reflects fewer queries when no promotion occurs, has not been prospectively frozen, and comes with materially elevated promotion under out-of-class marginal-null stresses. C2/C6 were already developed and prior-art screened; this replay does not make them new. On corrected real source clusters they do not distinguish from Gated+front. See `CORRECTED_REPLAY_AUDIT.md`.

Corrected null rates must be classified by target. Ordinary iid `V_null` yielded 0/1000 promotions for adaptive Gated and 1/1000 for each front/pace variant. Markov-persistent streams test a marginal/exchangeable-null robustness target; because conditional signs depend on past under that generator, these rates are not evidence of invalidity under a conditional-mean theorem. Conversely the order-2 and semi-Markov OOC controls are expressly outside the first-order homogeneous-Markov class; C2/C6 rates of 12.6–21.6% there constrain robustness claims but do not refute an in-scope guarantee. No empirical rate proves theorem validity.

Primary sources for the closest methods include Xu et al.'s official NeurIPS publication ([abstract](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6eb05d8bc6bd7bb6868c64b5802125bd-Abstract-Conference.html), [paper](https://papers.nips.cc/paper_files/paper/2024/file/6eb05d8bc6bd7bb6868c64b5802125bd-Paper-Conference.pdf)), restart e-detectors ([paper](https://nejsds.nestat.org/journal/NEJSDS/article/59/read)), and repeated/symmetric change detection ([DAS-CUSUM paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12002415/)). These links support prior-art context, not a comprehensive literature search or an originality guarantee.

## Falsification needed before reconsidering a method claim

Use one frozen reversal family and compare E_rb unchanged, E_rb with matched alpha, E_rb with the proposed cost-to-go addition, two-sided SR/CUSUM, and no rollback. Match start grid, horizon, released-label budget, delay, query cost, switching cost and allowable information. If the proposed addition does not improve paired net cost without unacceptable correctly specified null errors, stop the method track. The new 20-block replay is post-development and compared existing E_rb to matched RMM only; it did not perform this falsification set.
