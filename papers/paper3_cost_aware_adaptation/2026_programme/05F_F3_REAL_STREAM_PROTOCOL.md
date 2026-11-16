# F3 real-stream check: protocol fixed before any F3 run on real losses (2026-11-16)

Status: pre-specified, single run. Not a confirmation in the sense of 04F: every stream below was
already exposed to Papers 1/2 or the Atlas/sprint work, so results are labelled
EXPOSED_STREAMS_FROZEN_CONFIG. No F3 arm, comparator or parameter was ever run or tuned on them.
The sealed group `civic_records_sealed` and the `c4_sealed`/`saes_dev` caches are not used (they
are not on this machine and the sealed group stays unopened).

## Data (cached paired 0/1 losses, 2000 events per episode; read-only)
`data/atlas_v2_losses/`: airlines (50 episodes), bank (8), criteo (50), elec2 (4), openml_ldpa (32),
rialto (16), spam (1), uci_occupancy (4), weather (3). `data/sprint_fresh_losses/`: appliances (6),
beijing_pm25 (14), bike_hour (6), household_power (20), metro (16). 14 streams, 230 episodes.
Known before the run (descriptive stats from the READMEs and a per-stream mean of l0 - l1 computed
on 2026-11-16 to choose nothing): the challenger is worse on airlines and bank and better on the
other twelve. All tasks are binary with 0/1 loss, so the two models' predictions differ exactly
when their losses differ; the disagreement flag g_t = 1{l0 != l1} is observable before the label.

## Problem instance (the repo's existing real-stream scenario, `transfer.sim.PRIMARY`)
One episode = one run. T = 2000, B = 200, c_q = 0.05, switch fee k = 5. Label delay per stream as
used by earlier work: 24 (metro, beijing_pm25, bike_hour), 144 (appliances, household_power); for
the atlas streams `REAL_DELAYS` of `scripts/failure_atlas_v2/run_atlas_v2.py`: spam 50, weather 1,
elec2 48, and 100 for the rest (corrected 2026-11-16 before any run: the first version of this
file said 100 for all atlas streams). Features x are zeros. 20 policy seeds per episode (dev block offsets 60000-60019).

## Arms (frozen; nothing tuned on these streams)
The arm specs of `configs/paper3/f3_confirmation_arms_v1.json` with their simulation-tuned
parameters unchanged, except that the budget is restated in the same headroom terms:
R = 2k + h with h in {6, 14, 24, 50, 100} (h = 6, 14, 24 are the simulation budgets 12, 20, 30 at
k = 3; 50 and 100 are added because the horizon is 6.7 times longer). F3 arms per h: `f3_pi1`
(full sampling), `f3v2d` (paced sampling, delta = .05), `f3v2_blind8` (h = 14 only, as frozen).
Comparators: never, wald_cut, cusum, gate_wald, cusum_rb_h4, cusum_rb_h8, stoploss at each R.
The v2 window parameter is the declared delay.

## Feedback conditions
(a) clean: the stream's own constant delay. (b) adverse dropout: labels unfavourable to the
challenger are never released with probability .6 (the `dropout_adverse` mechanism). (c) adverse
delay: labels unfavourable to the challenger are delayed by a further 400 events. (b) and (c)
corrupt only the feedback, not the losses.

## Reported (all of it, whatever the outcome)
Per stream and condition: mean J per arm; Delta J vs wald_cut and vs never with an
episode-cluster bootstrap 95% CI (streams with fewer than 6 episodes: point values only);
sup-harm q95/q99/max; violation rate of each budget arm and exceedance rate of each R for the
comparators, with Wilson intervals over runs; labels; deployed fraction. Pooled: equal weight over
the 14 streams, and separately over the 2 harmful and the 12 beneficial streams.

Expectations stated in advance: Theorem 2 predicts zero violations for `f3_pi1` in every
condition and at most 5% for `f3v2d`. No prediction is made about mean cost relative to wald_cut.
