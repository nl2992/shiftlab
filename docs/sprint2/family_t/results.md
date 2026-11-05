# Family T results (Sprint 2)

This report consolidates existing outputs; no family run was repeated. The detailed candidate ledger
is [ledger.json](ledger.json), the design and adaptations are documented in [README.md](README.md),
and raw outputs are gitignored under `outputs/sprint2/T/`.

## Evidence inventory

- Development screens `devA`, `devB`, `devC`: 20 seeds per synthetic regime, seed base
  `2026110701`, alpha `.05`. `devA` tests evidence modules on CAMS, Model Picker, and Model Selector
  hosts and includes D1/D2/D5/D6 baselines. `devB` tests gated/DISCERN/T6 combinations. `devC` is an
  earlier variant comparison, useful as a sensitivity screen but not interchangeable with the final
  devA configuration.
- Track R uses the eight-point `bench2.ALPHA_GRID`. Seven dedicated `R_dev_a*` runs cover all
  values except `.05`; the development `devB` run supplies alpha `.05`. Eight `R_eval_a*` runs
  exist on a separate seed base, but contain only `T:cams/a5b`, D2, `T6:a5bxC2`, and C2. T3 was
  calibrated on development at `.05` but has no held-out Track-R evaluation or cost/risk curve.
  See `trackR.md/json` for the subset that was actually evaluated.
- Real fresh: 3 policy seeds on five streams; summary in `real_fresh_summary.json`.
- Twin streams: one policy seed for each supplied twin split; summary in `real_twin_summary.json`.
  These are reused known-null constructions, not unseen independent validation.

Run commands are preserved in `outputs/sprint2/T/cmd_dev.sh`, `cmd_stageC.sh`, and `cmd_stage2.sh`.
The predeclared parameter selection, intended null classes, and common-contract adaptations are
recorded in the family README.

## Candidate findings

| Candidate | Result |
|---|---|
| **T1: Model Picker + improved mechanism** | Coverage reconciled: final devA includes `T:mp/a5b` against the Model Picker adapter, D1, and D6:mp; `contrasts.json` includes all three contrasts. Mean alternative J: 397.7 for T:mp/a5b, 354.4 for Model Picker adapter, 369.5 for D1, and 377.2 for D6:mp. Thus T:mp/a5b is worse by about +43.4, +28.2 and +20.5. The A5b adaptive addition is neutral to the base T:mp/a5b setting (+0.1 [-1.7,1.9]). devC compares earlier `a5b1`/QSG/H2/H4 variants and is a separate sensitivity run. **The required comparisons were done; the candidate did not improve costs.** |
| **T2: Gated Deployment + evidence** | A5b evidence has 0/20 promotions on each of the four dev null screens and dev mean alternative J 395.7. `env8` is scoped to rho<=.8 and has 6/20 promotions on the rho=.95 screen; the QSG/front and front-loaded versions show the expected risk/cost trade-off. No uniform real-stream gain; transfer is heterogeneous. |
| **T3: corrected DISCERN + evidence** | A5b/no-front mean J 399.0 versus `discern_design_floor` 401.1 (difference -2.1 [-6.8,2.6]); front version 391.8 versus design-floor+front 405.2 (difference -13.5 [-20.1,-6.8]). Historical selected-port contrasts versus `choe_ramdas_eb+front` are unfavorable (+26.9/+19.7), and same-seed selection is unadjusted. This is mixed, within-host adapter evidence, not a general published-method claim. Track-R has no held-out T3 evaluation. env8 has 5–6/20 rho=.95 promotions; AND variants incur high costs. |
| **T4: CAMS evidence-module competition** | The unmodified CAMS adapter has lowest dev alternative cost (350.5) but severe null promotions (20/20 F0 null, 10/20 F0 worse, 19/20 and 19/20 on rho=.8/.95). More conservative evidence modules lower false promotions at higher costs: `T:cams/cmean` J 385.5, `cmean_s` 383.7, A5b 393.6. Twin rates vary by stream and are low-replication. |
| **T5: shared/fixed evidence wrapper transfer** | A5b fixed settings transfer procedurally to MP/MS with no promotions in the four dev null screens, but cost more than host adapters: MP 397.7 vs 354.4; MS 395.8 vs 347.0. The env8 module produces 4/20 rho=.95 promotions on each host, consistent with its rho<=.8 declared region being exceeded. No economic or broad validity gain is shown. |
| **T6: evidence x acquisition interaction** | For A5b x C2, interaction estimate +0.8 [-1.5,+3.0] and acquisition effect at best evidence -0.6 [-1.9,+0.7]; this does not establish interaction. T6:a5bxC2 has 0/20 promotions on the four dev null screens and mean alternative J 391.1. Track-R's selected R20 point has risk .087 [.043,.170] and cost 374.2 [368.7,379.8] at alpha .5. Fresh-stream differences vs A5b are mixed; twin estimates use one seed per split. |

For T2/T3/T5, the false-promotion fractions above are empirical development rates, not formal guarantees.
The observed .95-screen behavior is particularly important for methods whose guarantee declares a
rho<=.8 region.

## Comparator audit and limitations

Some historical tables describe `xu_acquisition_only` as certified/published. It is only the
acquisition component combined with ShiftLab's own certificate and cannot be used as evidence against
Xu et al.'s published risk-control method. Comparisons to `choe_ramdas_eb+front` in the generated
summaries are also exploratory: the comparator was selected from the tested set, and older summaries
do not correct uncertainty for that selection. Preserve those tables as historical output, then
produce explicitly amended contrasts with the corrected comparator classes before using “best
certified” language. These results do not establish published-SOTA superiority.

Real stream cost differences use short, finite streams with three seeds; twin summaries use one seed
per split. Neither analysis identifies causal shift dates or supports universal effectiveness claims.
The Track-R starred frontier is restricted to the tested methods and alpha grid, and selected
operating points are not confirmatory risk guarantees.

## Assessment

T1 comparison coverage is complete and its tested mechanism loses to the requested baselines on the
development economic metric. T2/T3/T4/T5 provide informative host-by-evidence compatibility and
dependence-misspecification results, but not a single general winner. T6 shows no measurable
evidence/acquisition interaction at the tested precision. **Keep the family as scoped development
evidence; correct comparator classifications and selection-aware analyses before drawing any
confirmatory or SOTA conclusion.**
