# B3+ consolidated results

All numbers below are computed from saved per-episode records under
`docs/promising_directions/results/b3_plus/` by
`/private/.../scratchpad/summarise.py` (reproduced by
`scripts/promising_directions/b3_plus_analysis.py`). Nothing is hand-entered.
Paired on episodes and on query-randomisation seeds with P3b, seed base `20261101`.
Bootstrap level: episodes when `K >= 5`, seeds when `K < 5` (flagged LOW-POWER).

## 1. Phase 1 selection (synthetic worlds only; locked windows not read)

Four worlds from the B1 simulator, `T = 2000`, `B = 200`, `c_q = 0.05`, 400 seeds.
Net-cost difference versus P3b, bootstrap over seeds.

The spec's exponential "decay" relevance shape was found to be **wrong in a way that matters**:
early in a segment `LCB = 0`, so `gap = c_s + Cq_future` and
`exp(-gap/(kappa*c_s)) ~ 0.37`, which *cuts* the query rate below P3b's exactly when no evidence
has accrued. Distance from the break-even boundary is the wrong relevance signal, because a
large positive gap means "undecided", not "irrelevant". Replaced by a gate: withhold spend only
in the one unambiguous case, where no label can change the decision.

A second finding: gating on the cumulative margin grid alone starves acquisition *after* a
change point, because the grid keeps certifying "challenger worse" long after the challenger has
improved (world W1 is worse-then-better at `tau = 600`). Requiring the recent discounted
advantage to agree (`gate_recent`) releases the gate promptly. Selected: `gate_recent`,
`r_max = 1.0`, so the rule can only ever withhold spend, never exceed P3b's pacing.

| World | P7a (promotion) | P7b (acquisition) | P7 (both) | P4ref |
|---|---|---|---|---|
| W1 persistent improvement, `c_s=20` | +24.9 LOSS | **+2.4 LOSS** | +26.9 LOSS | +186.5 LOSS |
| W3 improvement then reversal, `c_s=20` | -7.2 WIN | **-2.8 WIN** | -9.3 WIN | -12.0 WIN |
| W2 challenger worse, `c_s=20` | 0.0 | **-0.8 WIN** | -0.8 WIN | 0.0 |
| NULL exact null, `c_s=20` | -0.6 WIN | **-0.1 WIN** | -0.7 WIN | -0.6 WIN |

Reading at selection time: acquisition (P7b) is a small consistent gain in three worlds and a
small loss in one; break-even promotion is a large *conditional* effect, strongly positive under
reversal and strongly negative under persistent improvement. P7b was therefore selected as the
primary method and the promotion gate retained only as an ablation.

## 2. Phase 3/4 real data, primary configuration S0

`T = 2000`, `B = 200`, `c_q = 0.05`, `c_s = 5`, protocol delays. Net cost; `vs P3b` is the
paired difference with its 95% CI.

| Stream | K | P0 | P3b | **P7b (B3+)** | vs P3b | labels vs P3b | P6 vs P3b |
|---|---:|---:|---:|---:|---:|---:|---:|
| spam | 1 | 849.00 | 254.09 | **254.09** | **0.000** (exactly identical) | 0.0 | +61.9 LOSS |
| rialto | 16 | 202.06 | 103.73 | **103.73** | **0.000** (exactly identical) | 0.0 | +19.2 LOSS |
| weather | 3 | 504.00 | 475.77 | **475.77** | **0.000** (exactly identical) | 0.0 | **-10.2 WIN** |
| airlines | 50 | 776.80 | 781.40 | 781.02 | -0.385 WIN | -7.7 | **-6.0 WIN** |
| bank | 8 | 419.38 | 428.19 | 427.61 | -0.574 WIN | -11.5 | **-6.1 WIN** |
| elec2 | 4 | 389.50 | 397.58 | 397.56 | -0.018 WIN | -0.4 | **-9.6 WIN** |
| criteo | 50 | 693.92 | 699.19 | 699.19 | 0.000 | 0.0 | **-7.1 WIN** |

Promotion-gate variants at S0, on the three central streams: P7a and P7 **lose** on all three
(spam +23.8, rialto +9.0, weather +17.6). P4ref loses far more (spam +127.9, rialto +106.3,
weather +37.2). PCT, the point-estimate cost-aware threshold, is **identical to P3b** on every
stream: once the e-process has crossed `1/alpha` the point-estimate break-even gate essentially
never binds.

## 3. Sensitivity, the configurations where the mechanism predicted benefit

S2 (`c_s = 20`, cost awareness should matter most) and S4 (`c_q = 0.10`, label savings should
matter most), three central streams. `vs P3b`:

| Stream | config | P7b | P7a | P7 | P6 |
|---|---|---:|---:|---:|---:|
| spam | S2 | **0.000** | +26.5 LOSS | +26.5 LOSS | +61.9 LOSS |
| rialto | S2 | **0.000** | +14.4 LOSS | +14.4 LOSS | +19.2 LOSS |
| weather | S2 | **0.000** | +19.6 LOSS | +19.6 LOSS | **-15.6 WIN** |
| spam | S4 | **0.000** | +23.8 LOSS | +23.8 LOSS | +54.6 LOSS |
| rialto | S4 | **0.000** | +9.0 LOSS | +9.0 LOSS | +14.2 LOSS |
| weather | S4 | **0.000** | +17.6 LOSS | +17.6 LOSS | **-16.6 WIN** |

Raising the switching cost fourfold and doubling the label price changes nothing for P7b on the
three central datasets, and makes the promotion gate worse, not better.

## 4. Why P7b is exactly identical to P3b on the central streams

Not a bug; the mechanism is understood and was predicted in
`B3_PLUS_PROTOCOL.md` amendment (a) before these runs. The hopeless gate fires only when
`UCB_t * (T - t) < c_s` **and** the recent discounted advantage is negative. With grid step
`0.01`, `c_s = 5` and `T - t` up to 2000, the first condition needs `UCB_t = 0`, i.e. the
challenger must be *certified worse*. On spam, rialto and weather the challenger is genuinely
better, which is exactly why P3b wins there, so the gate never fires and every issued propensity
equals P3b's. The small wins on airlines, bank and elec2 are the gate firing where the
challenger is in fact not better.

## 5. SUPERSEDED by section 8: the first B3+ attempt gated the wrong case

The conclusion below was correct for the method as then implemented, and is kept as
the record of that negative result. Section 8 reports the corrected method, which does
work. The diagnosis in section 4 is what led to the correction.

### 5.1 Original (superseded) reading

`B3_PLUS_PROTOCOL.md` section 9 fixed this reading in advance:

> **No contribution** if B3+ is indistinguishable from P3b everywhere and from P4ref on
> promotion.

That condition is met. On the three datasets the paper was to centre on, B3+ is bit-identical to
P3b in all three configurations tested; where it does act it is either economically negligible
(-0.02 to -0.57 on net costs of 390-780, i.e. 0.005% to 0.13%) or harmful (the promotion gate
loses on every central stream in every configuration). The protocol's stopping rule applies:
**the original P3b implementation will not be rebranded as a new algorithm, and no B3+ paper
claim is made.**

Both components are retained in the repository as negative results with a diagnosed mechanism,
which is itself a reportable outcome.

## 6. The finding that is actually live

Visible in the same saved records, and not a B3+ claim:

**A fixed-sample exact binomial test on ~50-60 disagreement labels (P6) beats the anytime-valid
sequential certification procedure (P3b) on 5 of 7 real streams, using roughly a third of the
labels.** At S0: weather -10.2, airlines -6.0, bank -6.1, elec2 -9.6, criteo -7.1, all with the
CI below 0. P3b wins only on spam (+61.9) and rialto (+19.2), the two streams where the
challenger's advantage is large. On weather the P6 advantage *grows* as labels get more expensive
(-10.2 at S0, -16.6 at S4) and as switching gets dearer (-15.6 at S2).

Interpretation to be tested rather than asserted: under a hard label budget, the labels an
anytime-valid procedure spends to keep its certificate valid at every stopping time are a real
cost, and that cost frequently exceeds the value of the optional stopping it buys. P6's stated
limitation is that its validity rests on exchangeable disagreement outcomes, which is assumed and
not guaranteed; any paper built on this must treat that asymmetry of guarantees as central
rather than as a footnote.

This is a structural/empirical finding about the price of sequential validity, not a new
algorithm. Whether it is developed into the ICML submission is a research-direction decision,
recorded here as open.

## 7. Status

- Phase 0 complete. Phase 1 complete (selection made, on synthetic only).
- Phase 2 complete (novelty recorded; P4ref identified as the true incumbent).
- Phase 3/4 complete for S0 on all 7 streams, and S2/S4 on the central 3. S1, S3,
  the four-stream S2/S4 extension, and the 1,000-event diagnostic were running at the time of
  writing and do not bear on the section 5 conclusion.
- **Phase 5-7 not started, and the B3+ manuscript is not written, because the pre-registered
  outcome rule says it should not be.**
- S5 (alternative model pairs) was never executable here: it needs the raw data root, a Windows
  path on another machine. Nothing was synthesised.

## 8. Correction: the settled-decision gate (P7s)

### What was wrong

"No label can change the deployment decision" has **two** cases. The first attempt implemented
only one:

- **hopeless** -- not yet promoted and the challenger is certified worse, so promotion is off the
  table;
- **settled** -- *already promoted* and the challenger is still ahead, so the deployed action is
  not in question and further labels buy only rollback insurance.

The hopeless case is **unreachable on exactly the streams where certified switching pays**,
because there the challenger is genuinely better. Worse, the first implementation carried a spec
deviation that hard-set `r = 1` whenever deployed on the challenger, which disabled the gate in
precisely the state where the opportunity lives. The diagnostics in section 2 were already
sufficient to see this and were not interrogated: P3b promotes at `t ~ 244` on spam and then
keeps buying labels for the remaining **1756** events at full pace, with promotion rate 1.00.

| Stream | P3b labels | promotion rate | mean promotion time | events after promotion |
|---|---:|---:|---:|---:|
| spam | 200.0 | 1.00 | 243.7 | 1756 |
| rialto | 159.2 | 1.00 | 425.1 | 1575 |
| weather | 178.4 | 1.00 | 988.1 | 1012 |

This is also the mechanism behind P6's advantage: P6 stops querying after its fixed batch.

### The corrected rule

`acq_shape = "settled"`, variant **P7s**. Post-promotion the margin grids are frozen, so LCB/UCB
are undefined there, but the recent discounted advantage `pst` is defined. Sign convention: the
released increment is `y = sgn * x` with `sgn = -1` once deployed on the challenger, so
`pst < 0` post-promotion means the challenger is **still ahead** (decision settled) and
`pst >= 0` is evidence of reversal.

    settled_t = (deployed on challenger) AND (pst_t < 0)
    inert_t   = settled_t                     if deployed on challenger
              = hopeless_t AND (pst_t < 0)    otherwise
    r_t       = r_floor if inert_t else r_max,     r_floor = 0.25, r_max = 1.0

`r_max = 1.0` means the rule can only ever *withhold* spend, never exceed P3b's pacing. The
`r_floor = 0.25` quarter-rate monitor is what keeps rollback detectable; synthetic selection
showed floors of 0.05 and 0 lose on persistent improvement (+5.15, +4.53) by starving rollback,
while 0.25 is neutral there (+0.46, CI straddling 0) and wins the other three worlds. Rollback
rate under reversal is preserved (0.21 versus P3b's 0.22 in world W3).

### Real-data result, three central streams

Paired with P3b on the same episodes and the same query seeds. Episode bootstrap for rialto
(K=16); seed bootstrap flagged LOW-POWER for spam (K=1) and weather (K=3).

| Stream | config | P3b | **P7s** | vs P3b (95% CI) | labels |
|---|---|---:|---:|---:|---:|
| spam | S0 | 254.09 | **252.86** | **-1.23** [-1.28, -1.18] | -24.6 |
| rialto | S0 | 103.73 | **101.59** | **-2.14** [-2.59, -1.66] | -42.7 |
| weather | S0 | 475.77 | **474.88** | **-0.89** [-0.92, -0.85] | -17.7 |
| spam | S2 (`c_s=20`) | 269.09 | 267.86 | -1.23 [-1.28, -1.18] | -24.6 |
| rialto | S2 | 118.73 | 116.59 | -2.14 [-2.59, -1.66] | -42.7 |
| weather | S2 | 490.72 | 489.83 | -0.89 [-0.92, -0.85] | -17.7 |
| spam | S4 (`c_q=0.10`) | 264.09 | 261.63 | -2.46 [-2.56, -2.36] | -24.6 |
| rialto | S4 | 111.69 | 107.41 | **-4.27** [-5.18, -3.32] | -42.7 |
| weather | S4 | 484.68 | 482.91 | -1.77 [-1.84, -1.70] | -17.7 |

Wins on all three streams in all three configurations, with the CI below zero every time. The
effect is invariant to `c_s` and scales **exactly** linearly in `c_q` (doubling the label price
doubles the gain), which is the signature of a pure label-saving mechanism and not a fitted
effect. Labels fall by 12% (spam, 200 -> 175), 27% (rialto, 159 -> 116) and 10% (weather,
178 -> 161), with promotion rate and switch count unchanged at 1.00.

Adding break-even promotion on top (**P7sp**) still **loses** on every central stream in every
configuration (spam +22.7 to +25.4, rialto +5.2 to +12.6, weather +16.9 to +19.6). The section 5
finding stands for that component: the promotion gate is harmful here and is not part of the
method.

### Effect size, stated plainly

Net-cost reductions are 0.5% (spam), 2.1% (rialto) and 0.2% (weather) at S0, rising to 0.9%,
3.8% and 0.4% at S4. These are **small**. What is solid is that they are consistent in sign
across every stream and configuration tested, paired at the episode level on the only powered
testbed, and produced by a mechanism that is transparent and predicts its own scaling.

### The caveat that must not be buried

**P7s does not close the gap to P6.** On weather, P6 beats P3b by -10.2 (S0) to -16.6 (S4) while
P7s manages only -0.89 to -1.77; P6 also still beats P3b on airlines, bank, elec2 and criteo. So
the honest ranking on four or five of the seven streams is P6 first, not P7s. P7s is an
improvement **on P3b**, in the regime where P3b is the right family of method at all (large,
persistent challenger advantage: spam, rialto). Any manuscript must report the P6 comparison in
the main table, not an appendix, and must state that P6's validity rests on an assumed
exchangeability of disagreement outcomes that the sequential procedure does not need.

## 9. On strengthening the evidence

Legitimate options, and their actual availability here:

- **More real streams.** The B3 protocol excluded outdoor (no eligible pair), noaa (next-hour
  label is not point-in-time), gas (exposed) and folktables/WILDS (not event streams), each for a
  stated methodological reason that still holds. Adding streams beyond the seven requires the raw
  data root, a Windows path on another machine, so it cannot be done in this worktree.
- **Shorter-horizon slices** raise the episode count for spam and weather but are splits of the
  same data, so they are a robustness diagnostic and **not** independent evidence. They must not
  be pooled with the 2,000-event results or counted toward K.
- **More query seeds** reduce seed-level noise only. They do not create episode-level power, and
  counting them as independent episodes would be a straightforward misrepresentation.

The binding constraint is that spam supplies one locked episode and weather three. No amount of
reanalysis changes that; only new data would.
