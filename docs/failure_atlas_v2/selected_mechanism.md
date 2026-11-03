# Failure Atlas v2: selected shared failure and its mechanism

2026-11-03. Evidence: synthetic discovery (`outputs/failure_atlas_v2/discovery_synth*`, 20 regimes x
100 paired streams, seed base 2026110301), real discovery (`discovery_real`, 9 datasets, 168
episodes x 20 policy seeds), development ablations (`dev_repair`, `dev_qsg_v1`, seed base
2026110311) and the controlled budget experiment (`mech_budget_B*`, seed base 2026110312). Full
tables: [atlas_synthetic_discovery.md](atlas_synthetic_discovery.md).

## Ranked shared failures

| rank | mechanism | families affected | economic size (per 2000-event episode) | reproduced on real data | repair feasibility |
|---|---|---|---|---|---|
| **M1** | **Certification latency under a binding budget** | the certified methods as run under a hard budget: off-policy CS (gated) and DISCERN (one family), SMCS, Xu betting, P7s (ours, prior); see the correction below on where the cause lives | +8 to +120 vs best uncertified on stationary-advantage cells (+10 F8, +8 F7_near_tiny at the low end); gated and DISCERN cost **more than never switching** on F0_better (426/429 vs 419) | yes: against the strongest certified method (SMCS) the gaps to the best uncertified are +44 spam, +35 openml_ldpa, +14 uci_occupancy, +17 rialto | high (acquisition + evidence wrapper) |
| M2 | False promotion and switching churn | all 8 uncertified: Model Picker, Model Selector, Online LLM Picker, CAMS, variance-min, Gong-Zhang, Qiu et al., Ryabchenko | +12 to +64 vs never-switch on null and dependence cells; 5-11 switches per episode | yes: airlines, bank, elec2 (2-5 switches, +10 to +30 vs never) | already solved by certification; the gap is M1 |
| M3 | No recovery after regime change | gated, DISCERN, SMCS (terminal verdicts); fast methods exposed to reversals | late onset: gated 398 vs Qiu 340 on F1_late_800; reversal: every promoting method pays | not testable (real streams carry no verified change times) | low: budget spent before a late change cannot be recovered |
| M4 | Strong serial dependence inflates promotion | all betting methods once sampling is dense | null promotion .24-.63 at rho=.95 for front-loaded variants | not testable | open (cycle-7 lesson stands) |

M1 is selected: largest, present in every certified family, reproduced on four powered real
streams, and directly repairable. Because the certified methods already solve M2, a certified
method without M1 dominates both families on the null/alternative mixture that real deployments face.

## Causal explanation of M1

Write `D` for the disagreement rate and `B/T` for the label budget per event. Every certified host
uses a budget-feasible pacer of the same form, `q_t = remaining / (expected remaining
disagreements)`, clipped below at `p_min`:

* gated and DISCERN share `PacedDisagreementAcquisition`;
* SMCS uses the P7a pacer;
* Xu maps the hard cap to a target rate `B/T`.

When the budget binds (`B < D T`), `q_t ~ B/(D T) < 1` throughout the horizon. Two things follow.

1. **Information arrives at rate `q D` per event (all hosts).** The expected number of events
   before `n` labels exist is `n/(q D)`, so the certificate fires `1/q` times later than the
   label information requires. The value of a promotion decays with remaining horizon `(T - t)`,
   so uniform pacing spends the budget where it is worth least.
2. **Horvitz-Thompson range dilution (gated, DISCERN, Xu).** Increments `w d` with `w = 1/q` are
   bounded only by the declared `1/p_min = 20`. A wealth-positive betting CS must cap its bet for
   that worst case (gated: `l1 (1 - wmax) + l2 <= 1/2`; DISCERN: `c = 1/p_min`; Xu: `lambda <= q/2`
   on `d/q`), so the evidence per label is far below the label's Kullback-Leibler information.
   DISCERN's range is fixed regardless of `q`, so it never certifies a 0.06/event advantage at any
   budget. SMCS escapes this (`lambda_s d/q_s = d/2`), but its fixed bet of 1/2 is mis-sized.

### Controlled test (stream fixed, budget varied)

F0_better (D = .2, p = .65, G = .06/event), 60 paired streams per budget:

| policy | promote B=100 | B=200 | B=400 | B=1000 | net B=200 | net B=1000 |
|---|---|---|---|---|---|---|
| gated | .00 | .07 | .93 | .98 | 425.8 | 361.4 |
| gated + QCE | .37 | .72 | .95 | .97 | 391.9 | 360.3 |
| gated + front only | .32 | .77 | .98 | .98 | 364.3 | 361.4 |
| gated + FLQ | .35 | .77 | .97 | .97 | 364.5 | 360.3 |
| DISCERN | .00 | .00 | .00 | .00 | 427.4 | 437.3 |
| DISCERN + QCE | .40 | .78 | 1.00 | 1.00 | 387.9 | 360.5 |
| SMCS | .62 | .80 | .82 | .85 | 372.4 | 371.6 |
| SMCS + QCE | .55 | .90 | 1.00 | 1.00 | 378.1 | 363.8 |
| Xu | .43 | .80 | .98 | 1.00 | 387.2 | 363.6 |
| QSG | .50 | .87 | 1.00 | 1.00 | 354.7 | 359.8 |

Gated's failure is caused by the budget forcing `q < 1`, not by too few labels: once `B >= D T`
(B=400, 1000) it certifies. When the budget does not bind, every repair converges to its host
(no cost of the repair there). Null promotion (F0_null) is <= .05 for every policy at every budget.

### Development ablation (repair minus host, 100 dev streams, F0_better)

| host | +QCE | +front only | +FLQ (both) |
|---|---|---|---|
| gated | -36.3* | -60.0* | -59.4* |
| DISCERN | -41.2* | 0.0 | -61.0* |
| SMCS | +2.4 | -16.2* | -18.9* |
| Xu | +2.7 | -19.1* | -19.1* |

(* paired bootstrap 95% CI below 0.) Front-loading carries the gain for gated, SMCS and Xu; QCE
is the necessary half for DISCERN. Full regime-by-host table: `outputs/failure_atlas_v2/dev_pairs.csv`.

## Repair (attachable): FLQ

`scripts/failure_atlas_v2/qce.py`. While the host is undecided, query every disagreement
(q = 1) until the budget is spent; feed the host's own CS or e-process the queried outcomes
`Y in {-1, +1}` with weight 1 (range 1 instead of `1/p_min`). Everything else of the host (bet
rule, stopping and deployment rule, delay handling, level) is unchanged.

Validity: under the pointwise conditional promotion null `E[d_t | F_{t-1}, d_t != 0] <= 0` for
all t, a predictable query rule that does not read the label leaves `E[Y_k | past] <= 0`, so any
bounded-mean e-process over the Y stream keeps level alpha (Ville). This is the same null the HT
construction protects. Under persistent serial dependence that null is false even when the
stationary mean advantage is zero (M4); front-loaded sampling, being dense in time, is more
exposed to it than paced sampling.

## Standalone candidate: QSG

`scripts/failure_atlas_v2/qsg.py`: QCE outcomes, a started-mixture Bernoulli e-process
(grid p' in {.55..95}, start weights 1/(k(k+1))) for promotion at alpha/2^cycle, a mirrored test
for discard and for rollback, front-loading while undecided and paced monitoring after a verdict.
It is the best certified method on most stationary-advantage dev cells (not F7_near_tiny, where
SMCS is lower by 1.1 [0.1, 2.3]); its rollback and started
mixture contribute little measurable gain (ablations in `dev_qsg_v1`), so its advantage over
host+FLQ comes from the sharper Bernoulli mixture evidence.

## Limitations carried forward

* The repair makes hosts without rollback promote earlier, which costs them on reversal and
  recurrent cells (dev: gated +60.9, DISCERN +64.5 on F3_reversal_800).
* Front-loading spends the budget before a late onset; no certified method in the suite handles
  late improvements as well as the uncertified Qiu et al. adaptation.
* No certified method, repaired or not, matches the uncertified methods' cost on clear stationary
  alternatives (QSG 356.5 vs Qiu 334.4 on F0_better dev). The claim is scoped to the certified class.

## Correction after independent review (2026-11-03)

See [review_discovery_algorithm.md](review_discovery_algorithm.md). The latency does not live in
the published inference algorithms. It lives in the hard-budget acquisition layer that every
published certified method needs and none specifies: the budget-feasible uniform pacers used here
(`PacedDisagreementAcquisition`, the P7a pacer, Xu's `B/T` target rate) are adapter choices.
"Range dilution" holds for the gated and DISCERN ports only, because they declared the worst-case
range `1/p_min`. With a predictable per-step range (`GatedAdaptiveRange`) or a design floor
(`DiscernDesignFloor`, `pi_min = .25`) both hosts get substantially stronger, and these stronger
re-ports are the comparators used in validation. For Xu the dilution claim was false (its bet
`lambda <= q/2` on `d/q` is scale-invariant), and SMCS's "QCE" is only a change of bet size.
The ">= 3 independent families" criterion is therefore met by the acquisition layer as deployed
(anytime-CS, e-elimination, active-testing betting, our B3+ policy), not by the papers' algorithms.
The budget experiment also changes label counts and HT variance together with q; it shows the
failure disappears when the budget stops binding, not a pure 1/q effect.
