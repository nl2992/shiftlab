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

## 5. Pre-registered outcome: NO CONTRIBUTION for the B3+ algorithm

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
