# R5 all-14-source real-stream cost replay

Registered 2026-11-05 before execution. This post-development descriptive replay extends the prior three-seed, seven-source R-family real run to all 14 registered paired-loss sources. All source datasets are already exposed in this sprint or earlier programmes; new policy seeds measure Monte Carlo variation and do not create independent dataset confirmation.

## Frozen question and comparison

At the existing real-screen operating configuration, does R5's risk-aware economic rule improve realized net cost over D2, A5b, the prior economic replacement comparator, `R:economic_stop`, CAMS, or the gated adaptive-range certificate across the registered real streams? The primary contrast is paired episode mean `J(R5)-J(D2)`. Other comparisons and component outcomes are descriptive. Net cost is `prediction loss + .05 * requested labels + 5 * switches`.

No stream is assigned an outcome-derived null, late-improvement, or reversal label. The nine Atlas caches have no verified causal event times or feature-publication timestamps. Although the five UCI sources retain chronology, these paired-loss replays do not identify counterfactual application utility or causal R5 value.

## Frozen execution

- Sources: nine Atlas caches (`rialto`, `spam`, `weather`, `openml_ldpa`, `uci_occupancy`, `airlines`, `bank`, `elec2`, `criteo`) and five UCI streams (`metro`, `beijing_pm25`, `bike_hour`, `appliances`, `household_power`), 230 stored episodes total.
- Policies: `R5`, `D2`, `A5b`, `economic_replacement`, `R:economic_stop`, `cams_adapter`, and `gated_adaptive_range+front`.
- 20 policy-randomness seeds per episode, seed base `2026110903`.
- Nominal alpha `.05`, matching the existing Family-R real-data screen. R5 uses the economic evidence module; alpha is relevant to comparator gates.
- Contract remains `B=200`, `c_q=.05`, `c_s=5`; source-specific delays are the `screen.py` real and fresh-real constants.
- Save records and manifest under `outputs/sprint2/round5/R5_all14_real20/`.

## Analysis and interpretation

Average seeds within each fixed episode, compute paired R5-minus-comparator cost differences per source with t intervals across chronological episodes, and report source-level cost, labels, switches, promotion rate, and equal-source mean summaries. With one episode for spam, no within-source interval is estimable. Consecutive episodes may be dependent; per-source intervals may be optimistic. Do not treat seeds as independent data sources or use evaluator-side real-gain proxies as truth. Report mixed and unfavorable results without changing the protocol.
