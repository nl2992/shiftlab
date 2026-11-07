# Failure Atlas v2: discover, repair, and test against SOTA

2026-11-03. Branch `claude/dazzling-wilbur-a3e951` (merges `research/b3-generalisation-icml` and
`research/atlas-local-checkpoint-2026-11-01`; all v1 and SOTA-programme results and stopped
verdicts are preserved untouched). Protocol: [../failure_atlas_v2_protocol.md](../protocol.md)
with Amendments 1-2. Status: **no SOTA result under the registered criteria.** A useful benchmark and a mechanism finding; the repair's gains are bought by failing the registered dependence-safety criterion (final audit: [review_audit_claim.md](review_audit_claim.md)).

## 1. What was run

| stage | data | seeds | rows |
|---|---|---|---|
| discovery, synthetic | 20 regimes, 10 failure families | 100 paired streams/regime, base 2026110301 | 2000 jobs x 15 policies |
| discovery, real | 9 cached loss streams, 168 episodes | 20 policy seeds, base 2026110302 | 3360 jobs |
| repair development | same 20 regimes | base 2026110311 | 2000 jobs x 28 policies (+ QSG v1, envelope) |
| mechanism | F0_better/F0_null, B in {100,200,400,1000} | base 2026110312 | 480 jobs |
| fresh validation, synthetic | 13 NEW regime instances (registered before running) | base 2026110399 | 1300 jobs x 35 policies |
| validation, real | 9 streams, episode-level inference | base 2026110398 | 1680 jobs x 28 policies |

Contract: T=2000, B=200, c_q=.05, c_s=5, alpha=.05, common simulator
(`scripts/promising_directions/sota/simulator.py`). Competitors: gated deployment (off-policy CS),
DISCERN-style, SMCS, Xu et al., Model Picker, Model Selector, Online LLM Picker, CAMS (constant
policies), variance-min (IPW), Gong-Zhang, Qiu et al., Ryabchenko/Attias-Roy adaptations, P7s (ours,
B3+), plus stronger re-ports of gated (`wmax_t = 1/q_t`) and DISCERN (`pi_min = .25`) added after
review. Sawade calibrated, Xu prediction-assisted and CAMS contextual need features and were not
run on loss-only streams. The Challenger (arXiv:2512.18390) has no runnable label-budget form; the
economic-replacement control is its closest analogue.

Fidelity fix found during this work: the DISCERN-style PrPl-EB CS dropped the `/4` in
Waudby-Smith-Ramdas `psi_E` (eq. 14), weakening that comparator fourfold in its variance penalty.

## 2. Unified atlas: the shared failures

Tables: [atlas_synthetic_discovery.md](atlas_synthetic_discovery.md); real discovery in
`outputs/failure_atlas_v2/discovery_real`. Two complementary failures cover the published suite:

* **M1 certification latency (certified methods).** Under a binding budget (B < D T) every certified
  method recognises a better challenger late: on F0_better gated and DISCERN cost more than never
  switching (426, 429 vs 419); SMCS, Xu and P7s promote at median events 665-993. Reproduced on
  real streams (vs strongest certified SMCS the uncertified methods are cheaper by +44 spam, +35
  openml_ldpa, +17 rialto, +14 uci_occupancy).
* **M2 false promotion and churn (uncertified methods).** All eight uncertified families promote on
  64-100% of null streams with 5-11 switches, costing +12 to +64 over never switching on null and
  dependence cells; reproduced on airlines, bank, elec2.
* M3 no recovery after change; M4 strong serial dependence inflates promotion of any dense sampler.

## 3. Selected mechanism

[selected_mechanism.md](selected_mechanism.md), corrected after review. M1 is caused by the
hard-budget acquisition layer every certified method needs and no paper specifies: budget-feasible
uniform pacing sets `q ~ B/(D T) < 1`, so certificates arrive about `1/q` later than the label
information allows, and (for the gated/DISCERN ports) a declared worst-case HT range caps bets.
Controlled evidence: with the stream fixed, gated promotes on 7% of F0_better streams at B=200 and
93% at B=400; when the budget stops binding (B=1000) every repair converges to its host.

## 4. Algorithms

* **FLQ (attachable).** `scripts/failure_atlas_v2_flq/qce.py`: query every disagreement while the host
  is undecided; feed the host's own CS the queried outcomes with weight 1 (QCE). Attribution:
  front-loading carries the gain for gated, SMCS and Xu; QCE is necessary for the original DISCERN.
* **QSG (standalone).** `scripts/failure_atlas_v2_flq/qsg.py`: QCE outcomes, started-mixture Bernoulli
  e-process (valid under the pointwise conditional null via Ville on `E_k + 1/(k+1)`), promotion at
  alpha/2^cycle, front-loading while undecided, paced monitoring and rollback afterwards.
* **QSG-envelope (negative result).** A declared Markov-persistence envelope restores safety at
  rho=.8 but loses most power (dev F0_better 397 vs 357 plain QSG vs 381 SMCS). Not pursued.

## 5. Results on fresh data

Full tables: [validation_synthetic.md](validation_synthetic.md), [validation_real.md](validation_real.md).

**Amendment-1 host-vs-repair outcome: met** (registered after development showed where front-loading wins; the original protocol primary claim, which also required three powered real wins and no null above the bound, FAILS). Repaired minus host, paired CI below 0 on the
six stationary validation alternatives: gated 6/6 (-6.6 to -123.9), DISCERN 6/6 (-7.3 to -127.7),
SMCS 5/6 (-5.0 to -45.5), Xu 5/6 (-9.9 to -32.3); on the strong gated re-port 6/6 (-6.2 to -93.3);
on the strong DISCERN re-port 0/6 (front-loading hurts it, +0.4 to +15.9).

**Strict certification criterion (Amendment 2): FAILED by every front-loaded variant.** Promotion
on V_null_dep_r8 (rho=.8 Markov null) is .13-.32 against the .094 bound (QSG .32); all pass on
V_null, V_worse and V_null_dep_r5 (<= .04). Among published methods SMCS (.13) and P7s (.12) also
fail; gated, DISCERN (both readings) and Xu pass.

**Head-to-head, QSG vs the strongest published certified method per regime** (selected on the same
seeds, SMCS included although it fails the strict criterion):

| regime | QSG - strongest published [95% CI] |
|---|---|
| V_better_a / b / c | -25.6 [-33.0,-18.2] / -7.4 [-10.5,-4.6] / -48.0 [-59.4,-37.1] |
| V_dep_better_r5 | -21.9 [-28.3,-15.5] |
| V_bursty | -19.4 [-27.8,-10.9] |
| V_near | -2.4 [-6.6,+1.5] (tie) |
| V_late_600 | **+8.3 [+2.2,+14.6]** |
| V_reversal_1000 | **+32.8 [+28.8,+37.1]** |
| V_recurrent | -1.5 [-6.1,+3.0] (tie) |
| nulls | +0.2 to +0.7 (label spend); V_null_dep_r8 +5.1 and promotion .32 |

**Real data** (episode-level; streams previously exposed, including a development run of the
repair): QSG vs the strongest published certified method is robust only on rialto (-3.1
[-3.9,-2.1], 15/16 episodes, p=7e-6). openml_ldpa (-15.7 [-37.5,-0.6]) is driven by one episode
(-290.6); without it -6.9 [-15.5,+1.6] (t-test p=.12). Ties on airlines, criteo, bank; point
improvements on low-power spam, uci_occupancy, weather. Real validation used 10 policy seeds, not 20.

**Strictly certified variants are not better.** The QCE-only variants that pass the registered
criterion (gated+QCE .04, DISCERN+QCE .03, Xu+QCE .05) tie Xu acquisition-only on 4/6 stationary
regimes, win V_bursty (-3.8) and lose V_dep_better_r5 (+2.2) and V_near (+1.3).

**Against uncertified methods** no certified variant matches their cost on clear advantages (e.g.
V_better_a best uncertified 370.6 vs QSG 408.2), while they lose by 9-23 on null cells.

## 6. Exact positioning (revised after the final audit)

> On fresh synthetic seeds under a binding budget, front-loaded acquisition with query-conditional
> evidence lowered net cost relative to the original host for every certified host except the strong
> DISCERN re-port, and QSG beat every published certified-method port by 7-48 per 2000 events on 5 of
> 6 stationary alternatives (Holm-adjusted), at the price of failing the registered false-promotion
> criterion under rho=.8 persistence (.32 vs .094), regressing on late-onset (+8) and reversal (+33)
> regimes, and losing to uncertified methods and the economic-replacement control (+10 to +41).
> Variants that meet the registered criterion are not better than Xu acquisition-only. On real data,
> one previously exposed stream (rialto) shows a small robust gain (-3.1).

This is **not a SOTA claim**: the cost gain is obtained by trading away the strong-dependence safety
that certification exists to provide. Comparators are ports (the strong gated/DISCERN readings are our
re-ports), not author code. Novelty is low (front-loading = DISCERN with pi=1; QCE = sequential sign
test on discordant pairs; started mixture ~ e-detectors). What stands: the atlas and harness, the
two-family failure map (latency vs churn), the mechanism (uniform pacing under a binding budget), the
DISCERN port fidelity fix, and the recorded negative results.

## 7. Reviews

* Discovery/algorithm review: [review_discovery_algorithm.md](review_discovery_algorithm.md)
  (native substitute; ARIS skills unavailable). It changed the comparators, the certification rule
  and the framing before validation rows were read.
* Experiment audit and result-to-claim review: [review_audit_claim.md](review_audit_claim.md).

## 8. Reproduce

    uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 100 --seed-base 2026110399 \
      --regimes V_better_a,V_better_b,V_better_c,V_dep_better_r5,V_near,V_bursty,V_null,V_worse,V_null_dep_r5,V_null_dep_r8,V_late_600,V_reversal_1000,V_recurrent \
      --extra v2_extra --out outputs/failure_atlas_v2/validation_synth   # plus validation_synth_strong, see protocol
    uv run --with tabulate python scripts/failure_atlas_v2_flq/analyze_validation.py
    uv run --with tabulate python scripts/failure_atlas_v2_flq/analyze_real.py
    uv run pytest -q tests/test_atlas_v2_qce.py

Raw records stay in `outputs/failure_atlas_v2/` (gitignored); frozen-run source hashes in
`outputs/failure_atlas_v2/validation_source_rev.txt` (commit 64ee5a4 for the frozen run; strong
re-ports added in the following commit).

## 9. Continue / pivot / stop

**Pivot: stop the SOTA framing.** Keep the atlas/harness as a benchmark and negative-result contribution. The repair is real and transfers across four certified hosts, but it is
bounded by the dependence-safety failure and the late/reversal regressions. If continued, run one locked fresh-seed test (per the final audit): a
persistence-robust certified variant vs Xu acquisition-only and tuned non-uniform pacing baselines, success = promotion <= .094 at rho=.8 and .95 and CI<0 on >= 4/6 stationary alternatives; stop if it fails. Candidate: a
dependence-aware density control (sampling gap tied to a declared or estimated persistence) that
keeps most of FLQ's speed; the declared-envelope attempt showed the naive version loses the gain.
An exploratory dev-seed probe after validation (`outputs/failure_atlas_v2/dev_gap_probe`, not a
claim) found the same trade for simple thinning: a minimum gap of 6 events between front-loaded
queries cuts QSG's rho=.8 null promotion from .24 to .04 but raises F0_better cost from 356.5 to
378.4 (SMCS 380.6) and bursty cost from 361.0 to 405.9. Safety under persistence and front-loaded
speed currently trade almost one-for-one.
Fresh independent real datasets (not previously exposed) are needed for a confirmatory real claim.
