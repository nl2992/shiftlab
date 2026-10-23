# Paired detection power planning

This planning analysis uses only the completed 60-seed matched-bound pilot. It does not reuse these seeds for evaluation. Cost-stabilized allocation was the candidate nominated for a future independent comparison.

Against uniform on boundary-local harm, candidate-only detections were 5, uniform-only detections were 1, and paired ties were 54. The observed detection-rate difference was +0.067; the one-sided exact McNemar p-value for equality of marginal detection rates was 0.1094.

Prospective calculations treat independent seeds as the sampling units and plug in the observed discordance rate (0.100) and candidate win fraction among discordant pairs (0.833). The exact power calculation sums over the binomial number of discordant seed pairs and applies the one-sided exact conditional McNemar rejection rule. These are optimistic plug-in values from a small pilot; they do not account for winner's curse or uncertainty in the nuisance rates.

|One-sided alpha|Target power|Fresh paired seeds required|Plug-in power at 60 seeds|
|---:|---:|---:|---:|
|0.0500|0.80|151|0.310|
|0.0500|0.90|195|0.310|
|0.0125|0.80|219|0.113|
|0.0125|0.90|274|0.113|

## Scope and decision

This McNemar calculation tests the easier null of no difference in marginal detection probability. It does not test the locked protocol's practical-margin hypothesis that improvement exceeds 0.10. The pilot estimate (+0.067) is below that margin, so these sample sizes cannot be cited as powering the registered practical claim. A future study must either improve and re-lock the candidate on development seeds before a fresh test, or preserve the +0.10 margin and perform a dedicated paired-risk-difference power analysis. Do not launch a confirmatory run using the pilot seed block.

Reproduce by running: uv run python scripts/power_analyze_matched_bound.py
