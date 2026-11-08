# Post-confirmation comparator panel: results

Protocol: [comparator_panel_protocol.md](comparator_panel_protocol.md), locked at `6fdfe239`
before any panel run. Raw records (gitignored): `outputs/qsg_methods_search/p1_tune/` (Stage 1,
seed base 2026110731, 40 seeds) and `outputs/qsg_methods_search/p1_confirm/` (Stage 2, seed base
2026110851, 100 seeds). The UPF-style adapter was ported byte-identical from
`origin/claude/shiftlab-methods-strategy-dba13e`, and its 13 tests pass here.

```bash
cd scripts/qsg_methods_search && uv run python analyze_p1.py ../../outputs/qsg_methods_search/p1_confirm/records.jsonl wald_l0.9_g0.2,hoef_l0.9_g0.45,smarg_l0.9_k0.2,dwell_l0.9_s5,upf_d0.95_m50
```

## Stage 1 family winners (selected in-sample on the D3 seeds)

wald λ=.9 γ=.2 (353.12) · smarg λ=.9 κ=.2 (355.68) · dwell λ=.9 k=5 (355.84) · hoef λ=.9 γ=.45
(356.04) · upf δ=.95 m=50 (383.61). EQSDp B on the same seeds scored 353.03.

## Stage 2 (fresh seeds, Holm over 10 contrasts)

| arm | comparator | Δ family (95% CI) | Holm p | Δ change | Δ guard |
|---|---|---|---|---|---|
| B `EQSDp_l0.9_g0.2` | Wald LCB | −0.05 [−0.28, +0.19] | 0.68 | +0.34 | −1.01 |
| B | Hoeffding LCB | **−2.52 [−3.20, −1.83]** | 4e-10 | −5.91 | +5.97 |
| B | horizon-scaled margin | **−2.01 [−2.47, −1.54]** | 1e-12 | −0.53 | −5.69 |
| B | dwell (k-streak) | **−2.03 [−2.57, −1.49]** | 2e-10 | +0.33 | −7.92 |
| B | UPF-style (Regol) | **−29.99 [−31.20, −28.78]** | 2e-70 | −44.36 | +5.94 |
| A `EQSDp_l0.95_g0.2` | Wald LCB | +4.55 [+3.91, +5.19] | 1e-24 | +8.80 | −6.06 |
| A | Hoeffding LCB | +2.08 [+1.54, +2.63] | 1e-10 | +2.55 | +0.92 |
| A | horizon-scaled margin | +2.59 [+1.83, +3.36] | 3e-9 | +7.93 | −10.74 |
| A | dwell | +2.57 [+1.77, +3.37] | 1e-8 | +8.79 | −12.97 |
| A | UPF-style | **−25.39 [−26.61, −24.17]** | 3e-63 | −35.90 | +0.88 |

Family means: B 354.12, Wald 354.17, scaled margin 356.12, dwell 356.15, Hoeffding 356.63,
A 358.72, tuned Gong–Zhang 362.07, Qiu 362.98, UPF-style 384.11.

## Verdict under the locked rule: **PARTIAL**

- **Arm B survives 4 of 5 families and ties the Wald LCB.** Per the protocol, the contribution
  is "a confidence-bound (uncertainty-scaled) payback hurdle", not "a Beta quantile". A Beta
  posterior quantile and a Wald bound with the same γ and discounting are interchangeable here.
- **Arm A fails** against every λ=.9 tuned family except UPF. Every comparator family selected
  λ=.9, so arm A's deficit mostly reflects its discount factor, not its hurdle: compare arm A vs
  arm B, +4.6. Arm A's C3 pass stands only against the comparators registered at C3.
- **UPF-style transfers poorly to this contract** (−25 to −30). Its periodised, warm-up-gated
  recursion cannot switch before round ~250 and reacts slowly to change. This is the T3
  adapter's behaviour, not a claim about native UPF.
- **Size of the remaining edge.** Over the best non-confidence-bound hysteresis rules (scaled
  margin, dwell), the edge is about 2 units per episode: 0.6% of cost and about 5% of
  expected-oracle regret (B: 40.8). That is small on cost and meaningful-to-small on regret.
  The larger gains (−5 to −10 vs tuned Gong–Zhang and Qiu; −30 vs UPF-style) are against the
  published-method adapters.

## Consequence for the paper claim

C2 is restated as follows. Economic model replacement under a hard, delayed, disagreement-only
label budget, using discounted paired evidence and a reversible remaining-horizon payback rule
gated by a confidence bound. The confidence bound may be a Beta quantile or a Wald bound; they
are equivalent. The method beats published-method adapters (Gong–Zhang-, Qiu- and
Regol/UPF-style) by 5–30 units. It beats simpler hysteresis forms (scaled margin, k-streak) by
about 2 units. Novelty stays NOVEL-INTEGRATION. The standalone method contribution is modest,
and C4 must show the edge over Gong–Zhang/Qiu-style adapters transfers to real streams.
