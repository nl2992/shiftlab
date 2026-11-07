# P4: dependence-model misspecification

## Round-5 HMM-null follow-up protocol (registered before run)

The development screen observed HMM-null promotions for A5b, so this follow-up quantifies Monte
Carlo variability on that named out-of-class generator. This is a stress test, **not** a validity
test: A5b's first-order stationary Markov guarantee does not cover the hidden-state mixture, and
P1_renew additionally requires i.i.d. observation gaps. The result cannot establish a theorem
failure or extend a guarantee.

* Generator: registered `P_hmm_null`, with `hmm_p=(0.3,0.7)`, T/B and costs unchanged.
* 1,000 seeds at Round-5 null base `2026110802`; common streams and paired policy randomization.
* Policies: `A5b,P1_renew,P1_union,P1_A5b_c10,D2,rmm:gated_deployment+RMM,P6_LRMD_U`.
* Report per-policy promotions with Wilson 95% intervals, mean labels and mean net J. No threshold
  changes, repeated testing, or post-result tuning; raw records stay under `outputs/`.

The run output and summary are appended below after completion.

**Generators.** The new generators are in `fam_p.PRegime` and were registered into `bench.SPRINT_REGIMES`
when `fam_p` is imported; registration is idempotent (`test_registered_and_import_clean`). They are
listed below; the semi-Markov null and the existing order-2 null come from `ooc_regimes`.

* first-order Markov: F5_dep_*, P_markov_null_r98, P_bursty_null_r8 (Markov signs with bursty
  disagreements)
* second-order: P_order2_null / P_order2_better (copy t-1 w.p. .5, t-2 w.p. .4), and O_null_order2
* semi-Markov: O_null_semimarkov, P_semimarkov_better (Pareto(1.5) run lengths, sign Bernoulli(.65)
  per run)
* hidden-state HMM: P_hmm_null (p_h in {.3, .7}, switch probability .01), P_hmm_better ({.45, .85})
* piecewise rho: P_piecerho_* (rho = .2 / .95 / .5 at events 0 / 700 / 1400)

The generators set the marginal p for each null/alternative as specified, so the marginal expected
gain is E[G_t] = dis(2p-1). This is not a pathwise or conditional identity for every generator:
in the HMM, p_t varies with the hidden state and only the stationary state mixture determines the
marginal p; piecewise-rho changes dependence while retaining its configured marginal p.

**Run.** 20 dev seeds, base 2026110701 (`outputs/sprint2/P/dev_syn`). This is not validation, and
a 20-seed rate has a wide CI (0/20 gives a 95% upper bound of about .16).

## False promotion on V2 nulls (marginal p = 1/2)

| policy | Markov r8 | r95 | r98 | bursty r8 | order2 (O) | order2 (P) | semi-Markov | HMM | piece-rho |
|---|---|---|---|---|---|---|---|---|---|
| A5b | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **.15** | 0 |
| D2 | .15 | .70 | .80 | .55 | .30 | .65 | .30 | .15 | .25 |
| QSG | .30 | .85 | .90 | .65 | .40 | .70 | .25 | .20 | .20 |
| RMM (gated) | .20 | .70 | .95 | .40 | .20 | .60 | .15 | .15 | .30 |
| gated_adaptive_range+front | 0 | .35 | .55 | .30 | .10 | .30 | .15 | .10 | .05 |
| xu_acquisition_only | .05 | .35 | .40 | .15 | .05 | .25 | .10 | .20 | .15 |
| choe_ramdas_eb | 0 | .35 | .25 | .30 | 0 | .10 | .05 | .05 | .05 |
| gated_deployment+QCE+front | 0 | .35 | .60 | .35 | .10 | .30 | .15 | .10 | .05 |
| discern_design_floor | 0 | .20 | .20 | .10 | 0 | .05 | 0 | .05 | 0 |

## Mean net cost J on misspecified alternatives (p = .65)

| policy | Markov r8 | order2 | semi-Markov | HMM | piece-rho |
|---|---|---|---|---|---|
| A5b | 417 | 410 | 383 | 364 | 375 |
| D2 | 349 | 356 | 351 | 349 | 346 |
| RMM (gated) | 362 | 374 | 362 | 360 | 381 |
| gated_adaptive_range+front | 360 | 374 | 355 | 349 | 361 |
| never switch | 421 | 405 | 408 | 421 | 423 |

## Reading

* **A5b.** It had 0/20 promotions on the tested out-of-class nulls except the HMM. The table also
  shows zero promotions for some certified ports; it does not establish that A5b is uniquely safe.
  The HMM
  breaks it because a hidden regime makes the conditional p swing between .3 and .7, which is not a
  persistent sign chain: within a regime, signs are i.i.d. with p != 1/2. Every method sits at
  .05–.20 there. This is a new A5b failure class.
* **D2, QSG and RMM.** Their iid-conditional evidence has elevated promotion rates across the listed
  dependence-misspecified nulls (.15–.95). In this screen, those rates co-occur with long sign runs
  or other dependence; the table does not identify run length as the causal mechanism or separate it
  from the broader model misspecification.
* **Certified ports.** They fail mainly at rho >= .95 and on bursty and order-2 nulls.
* **Power.** A5b's power loss under misspecification is largest on order-2 and Markov alternatives,
  where it is at or near never-switch, and smallest on HMM and piece-rho.
* **Which conclusion to draw.** In this 20-seed screen, A5b had zero promotions on the tested
  out-of-class nulls except the hidden-regime HMM (3/20). This is descriptive stress-test evidence,
  not a guarantee outside A5b's declared first-order Markov null. The HMM is a demonstrated failure
  class for this implementation under the tested settings; the other tested classes are not thereby
  certified as safe. The validity-power trade-off from Sprint 1 remains a useful empirical pattern,
  but this screen is too small to establish uniform behavior across dependence classes.

## Round-5 HMM follow-up result

The frozen 1,000-seed follow-up found **176/1,000 A5b promotions** (0.176, Wilson 95% CI
[0.154, 0.201]) on `P_hmm_null`. The matched first-order Markov methods A5b, P1_renew and P1_union
had 176, 54 and 44 promotions respectively; the P1 intervals are [0.042,0.070] and [0.033,0.059],
so both overlap the nominal .05 line. D2 and RMM promoted on 256 and 250 streams. Full costs and
intervals are in [`P4_hmm_round5.md`](P4_hmm_round5.md); raw records and the 1,000-job manifest are
under `outputs/sprint2/round5/P4_hmm_null1000/`.

This confirms the observed HMM sensitivity at higher Monte Carlo precision for A5b. Because this
generator violates A5b's declared null assumptions, the rate is not evidence against its in-class
guarantee. Likewise, P1_renew/P1_union's observed rates do not establish validity under HMM
dependence or outcome-dependent gaps.
