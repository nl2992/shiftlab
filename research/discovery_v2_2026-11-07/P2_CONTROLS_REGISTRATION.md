# P2 attribution controls — registration

Registered 2026-11-07 **before any full control run** (only a 1-seed metro ORIG smoke run, kept as
`outputs/discovery_v2_p2_controls/smoke_ORIG_metro_1seed/`, was executed to check the wrapper: it reproduced the registered metro
column, e.g. gated .006 vs .006, SMCS .038 vs .037, CAMS .834 vs .820). Motivation: the independent adversarial review of P2
(2026-11-07, summarised in `DISCOVERY_DECISION.md`) found that the twin null is null only over the training-split coin, that per-split
twin advantages are large (appliances split-level SD 0.0281 vs mean 0.0077; 16/20 splits |z|>2 under an iid z), and therefore that
"serial dependence" and "per-split fixed effect" are confounded in the P2 headline.

## Conditions (deterministic; `scripts/p2_controls.py`, seeds [20261107, dataset index, condition index])
| cond | transformation per episode | fixed effect | serial dependence | conditional null |
|---|---|---|---|---|
| ORIG | none (rerun at current code) | kept | kept | not guaranteed |
| PERM | joint random time permutation of (l0,l1) | kept | removed | not guaranteed |
| BSWAP | fair-coin swap of (l0,l1) per 100-event block | removed (in expectation) | kept within blocks | marginal only |
| ESWAP | fair-coin swap of (l0,l1) per event | removed | sign dependence removed | **exact** |

Runner: unchanged `scripts/sota_sprint/screen.py` (contract T=2000, B=200, c_q=.05, c_s=5, α=.05, registered delays), 3 policy seeds,
seed base 2026110620, all 5 datasets, all episodes. Policies: gated_deployment, discern_style, gated_adaptive_range,
gated_adaptive_range+front, discern_design_floor, SMCS+retain-incumbent, xu_acquisition_only, choe_ramdas_eb, choe_ramdas_eb+front,
gated_deployment+QCE, gated_deployment+QCE+front, A5b, model_picker_adapter, cams_adapter. Analysis: `scripts/p2_controls_analyze.py`
(split-cluster bootstrap, as the original; "breaks" = promote > .0936 with lower CI > .05, as the original K1).
`xu_acquisition_only` is reported but not counted as a published certified port. Code version: current HEAD of this branch, which does
**not** include the MOPE-interval / adaptive-range fixes on `codex/sprint2-leaderboards`; the five gated ports may be affected and are
flagged in every table.

## Frozen hypotheses
* **HP2-a (fixed-effect attribution).** If, over certified cells that break in ORIG, mean PERM/ORIG promotion ratio ≥ 0.75, the excess
  is mostly the per-split fixed effect, not serial dependence.
* **HP2-b (conditional validity).** Under ESWAP every certified port has promotion upper CI ≤ .0936 on every dataset. A failure would be
  evidence against a port's conditional validity (a genuine invalidity signal), subject to the MOPE-fix caveat.
* **HP2-c (dependence suffices).** Under BSWAP, ≥ 3 of the 10 certified ports break on ≥ 1 dataset ⇒ serial dependence alone, without
  a fixed effect, drives marginal-bound excess.
Decision rule for the paper framing: HP2-a true and HP2-c false ⇒ retitle P2 as a conditional-vs-marginal-null *fixed-effect* benchmark;
HP2-c true ⇒ the dependence framing survives; HP2-b false ⇒ report an invalidity finding first.
Evidence class: all streams are exposed real data ⇒ results are EXPLORATORY attribution evidence, not confirmation.
