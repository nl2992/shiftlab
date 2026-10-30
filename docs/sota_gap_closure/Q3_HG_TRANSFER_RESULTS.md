# Does HG's earlier detection translate into net economic benefit?
Paired differences of net regret (negative = first policy better), 120 paired seeds per scenario, bootstrap 95% CI, base costs:

| scenario | comparison | mean_regret_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|
| harmful_incumbent_delay50 | hg_switch - ph_switch | 26.5 | 14.5 | 39.1 | HG worse |
| harmful_incumbent_delay50 | hg_switch - hysteresis | 20.1 | 8.4 | 31.9 | HG worse |
| harmful_incumbent_delay50 | cert_switch - ph_switch | 17.9 | 4.7 | 31.7 | n.s. |
| harmful_incumbent_delay50 | hg_switch - frozen | -25.4 | -35.5 | -15.8 | HG better |
| near_tied_flip | hg_switch - ph_switch | -6.2 | -10.0 | -2.8 | HG better |
| near_tied_flip | hg_switch - hysteresis | -5.6 | -9.2 | -2.3 | HG better |
| near_tied_flip | cert_switch - ph_switch | -7.3 | -11.6 | -3.6 | n.s. |
| near_tied_flip | hg_switch - frozen | 11.1 | 10.0 | 12.6 | HG worse |
| no_worthwhile | hg_switch - ph_switch | -1.7 | -3.9 | 0.0 | n.s. |
| no_worthwhile | hg_switch - hysteresis | -1.6 | -3.9 | 0.0 | n.s. |
| no_worthwhile | cert_switch - ph_switch | -1.7 | -3.9 | -0.0 | n.s. |
| no_worthwhile | hg_switch - frozen | 10.1 | 9.9 | 10.3 | HG worse |
| perm_beneficial | hg_switch - ph_switch | 19.2 | 6.2 | 32.2 | HG worse |
| perm_beneficial | hg_switch - hysteresis | 12.3 | -0.5 | 25.2 | n.s. |
| perm_beneficial | cert_switch - ph_switch | 6.9 | -6.1 | 21.0 | n.s. |
| perm_beneficial | hg_switch - frozen | -38.2 | -49.8 | -27.6 | HG better |
| reversal | hg_switch - ph_switch | -12.7 | -23.2 | -2.5 | HG better |
| reversal | hg_switch - hysteresis | -10.3 | -19.9 | -0.9 | HG better |
| reversal | cert_switch - ph_switch | -16.8 | -28.4 | -5.9 | n.s. |
| reversal | hg_switch - frozen | 23.8 | 15.8 | 32.6 | HG worse |
| temp_beneficial | hg_switch - ph_switch | -9.4 | -16.9 | -2.9 | HG better |
| temp_beneficial | hg_switch - hysteresis | -7.4 | -15.1 | -0.4 | HG better |
| temp_beneficial | cert_switch - ph_switch | -10.8 | -18.0 | -4.6 | n.s. |
| temp_beneficial | hg_switch - frozen | 11.7 | 9.9 | 15.2 | HG worse |

**Answer: not in general.** In permanent-harm scenarios (`perm_beneficial`, `harmful_incumbent_delay50`) HG-triggered promotion has **higher** regret than Page-Hinkley-triggered promotion (CIs exclude zero) because at 10% labels it alarms later (it switches in 20% of seeds vs 30% for PH). In the transient, reversal and near-tied scenarios HG's lower false-alarm rate gives lower regret (CIs exclude zero); in `no_worthwhile` the difference is within noise. HG's advantage in the earlier Q1 study was power at matched *size* on held-out worlds with unlabeled-vs-labeled differences; once an intervention cost and a blind promotion action exist, the cheaper false alarm matters mostly when harm is transient. Disagreement-focused certified promotion beats PH in the transient, reversal and near-tied scenarios, is not distinguishable from PH under permanent harm, and is **worse than PH in the delayed-harm scenario** (+17.9, CI excludes 0); it has essentially zero false promotions.
