# Failure Atlas v2 protocol: discover, repair, and beat SOTA

Registered 2026-11-03, before the discovery sweep was inspected and before any repair was run beyond
a 6-seed plumbing smoke (recorded below). Supersedes nothing: Failure Atlas v1 (cycles 1-7), the
SOTA programme and every stopped-experiment verdict remain as recorded. Result namespace:
`outputs/failure_atlas_v2/` (raw, gitignored) and `docs/failure_atlas_v2/` (tables, decisions).

## Contract (v2 primary)

| item | value |
|---|---|
| horizon T | 2000 events |
| hard label budget B | 200 (pathwise, enforced by the simulator) |
| label price c_q | 0.05 |
| switching cost c_s | 5 |
| anytime level alpha | 0.05 where a method has one |
| net cost J | prediction loss + c_q * labels + c_s * switches |
| seeds | 100 paired streams per synthetic regime; 20 policy seeds per real episode |
| simulator | `scripts/promising_directions/sota/simulator.py` (release-before-act, frozen issue propensities, delay >= 1) |

The original Atlas v1 configuration (T=1000, cycle-7 grid) is untouched and remains the historical
record; v2 numbers are never pooled with it.

## Seed namespaces

| use | seed base |
|---|---|
| synthetic discovery | 2026110301 |
| real discovery (policy randomness; streams are the cached B3 episodes) | 2026110302 |
| repair development / ablation | 2026110311 |
| fresh synthetic validation (new regime instances, perturbed parameters) | 2026110399 |
| fresh real validation (policy randomness; independent datasets where available) | 2026110398 |

## Competitors

All existing ports in `scripts/promising_directions/sota/competitors`, named per
`docs/promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md`: gated deployment (off-policy CS),
DISCERN-style, SMCS + retain-incumbent, Model Picker adapter, Model Selector causal adapter, Online
LLM Picker, Xu acquisition-only, CAMS (constant policies only), variance-min + streaming IPW,
P7s (ours, B3+), plus the Atlas v1 R6 adaptations ported to the simulator: Gong-Zhang paid
observations, Qiu et al. delayed movement, Ryabchenko/Attias-Roy capacity scheduling. Controls:
never-switch, development-tuned economic replacement. Not runnable on loss-only streams (no
features): Sawade calibrated, Xu prediction-assisted, CAMS contextual. "The Challenger"
(arXiv:2512.18390) is an optimal-stopping formulation without a label budget or delayed release;
the economic replacement control is its closest runnable analogue and is labelled as such.

Fidelity fix recorded before the sweep was analysed: the DISCERN-style PrPl-EB CS dropped the `/4`
in Waudby-Smith and Ramdas's `psi_E` (eq. 14 of arXiv:2010.09686) while keeping the factor 4 in
`v_i`, inflating the variance penalty fourfold. Fixed in `certificate_stops.py`; null coverage after
the fix: ever-miss 0.013 over 1000 Bernoulli(.5) streams of length 1000 at delta .05. DISCERN rows
of the discovery sweep that predate the fix are re-run and the old rows discarded.

## Regimes

`scripts/failure_atlas_v2/regimes.py`, 20 locked regimes in 10 families: stationary
better/null/worse; late improvement (onset 400/800/1200); transient; reversal (800/1200);
recurrent; Markov sign dependence (null rho .8/.95, better rho .8); delay 400; near-indistinguishable
(G = .032, .012); rare informative disagreements (dis .03, p .9); high disagreement; bursty
disagreements. Real: the nine cached B3 loss streams (rialto, openml_ldpa, airlines, criteo, bank,
elec2, weather, spam, uci_occupancy). Real streams carry no causal change labels; their realised
mean advantage is used only as an evaluator-side descriptor.

## Discovery question and decision rule

A failure is **shared** if it appears, with a paired 95% CI excluding zero against the strongest
applicable competitor or a feasible reference, in at least three independently developed
algorithm families (`SUITE_INFO` families) and in at least two regimes. Mechanisms are ranked by
reproducibility, economic size, prevalence across families, repair feasibility and novelty.

## Repair evaluation (pre-specified)

For a modular repair R and each host method H it attaches to, report `J(H)` and `J(H+R)` on
identical streams, feedback, budget and costs, with paired unit-bootstrap CIs. Ablate each
component of R. Strongest applicable published comparator for a certified repair = the lowest-cost
published method in the same regime that controls false promotion at alpha on the null regimes
(empirical null promotion rate <= alpha + binomial 2 SE). Uncertified methods are reported as
separate comparators with their null promotion rates, never silently excluded.

**Primary claim (to be confirmed on fresh validation seeds, then real data):** on stationary or
slowly varying alternatives with budget-forced query probability below 1, H+R has lower mean net
cost than H for every certified host, and the best certified H+R has lower cost than the strongest
applicable published comparator, while null promotion rates stay within the alpha + 2 SE bound.
Success margin: paired CI upper end < 0 in at least 4 of the 7 synthetic `alt` regimes and in at
least 3 powered real datasets; no null regime with promotion rate above the bound.

## Pre-run disclosure

Before registration, a 6-seed plumbing smoke on F0_better, F0_null, F5_dep_null_r8 and
F7_near_better ran the QCE variants (`outputs/failure_atlas_v2/smoke_qce`). It showed gated+QCE
certifying where gated did not. Those seeds (discovery base, 6 streams) are excluded from every
confirmatory comparison.

## Amendment 1 (2026-11-03, after the development sweep, before any validation run)

Development evidence (`outputs/failure_atlas_v2/dev_repair`, seed base 2026110311) changed the
attribution of the repair. Front-loaded acquisition (q = 1 on disagreements while the host is
undecided) carries most of the gain for gated, SMCS and Xu; query-conditional evidence (QCE) is
necessary for DISCERN, whose fixed `c = 1/p_min` range is unaffected by q. The attachable repair is
therefore registered as **FLQ = front-loaded acquisition + QCE**, with both single-component
ablations reported. Development also exposed two regressions that are carried into validation as
registered secondary outcomes, not hidden: (i) hosts without rollback lose on reversal/recurrent
cells because they promote earlier; (ii) dense front-loaded sampling raises promotion under strong
Markov persistence (rho >= .8), where the pointwise conditional null is false although the
stationary mean advantage is zero.

QSG v0 had a state bug (promotion reset the undecided flag, so the rollback test kept
front-loading and exhausted the budget). Fixed before validation (v1); v0 dev rows are retained
and labelled.

**Validation set** (`VALIDATION` in `regimes.py`, 13 new parameter instances, seed base
2026110399, 100 streams each) and **frozen policies**: the four certified hosts, each host +FLQ,
QSG v1, QSG-r25, P7s, every published uncertified competitor in the suite, never-switch and
economic replacement.

Registered primary outcome: per host, `J(H+FLQ) - J(H)` on the six stationary `alt` validation
regimes (V_better_a/b/c, V_dep_better_r5, V_near, V_bursty); success = paired 95% CI upper end
below 0 in at least 4 of 6 for at least 3 of 4 hosts. Secondary: best certified FLQ variant or
QSG vs the strongest published certified method (lowest mean cost among gated, DISCERN, SMCS, Xu)
in each regime; null promotion on V_null, V_worse, V_null_dep_r5 must be <= .05 + 2 SE;
V_null_dep_r8, V_late_600, V_reversal_1000 and V_recurrent are reported as stress regimes.
