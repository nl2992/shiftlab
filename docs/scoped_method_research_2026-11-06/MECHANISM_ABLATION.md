# Mechanism and ablation report

## Late improvement

WP1's retrospective late class contains 10 episodes from five clusters. RMM improves point estimates over its certificate host, but all four host-level 95% source-cluster intervals against the selected best certified comparator cross zero. RMM-minus-E_srr differences range from +4 to +9 (positive favors E_srr under the report's convention); no host shows a significant RMM advantage. E_srr's continued acquisition ablation is beneficial on the late class (−40.5 [−69.4, −6.3] for E_srr versus its no-acquisition version). Thus continued acquisition is a plausible driver, but RMM's special restart mixture is not established as the operative real-world advantage.

The Atlas synthetic findings show sensitivity to label budget: Gated promotion rises from 7% at B=200 to 93% at B=400 in the cited M1 comparison. However, changing B changes both label count and estimator variance; it is not a controlled isolation of delay or label pacing. The corrected synthetic validation also reports failed strict null criteria for candidate variants (e.g. QSG rho=.8 promotion .32 vs cap .0936). Do not claim validity from alternative-regime performance.

## Reversal and rollback

The post-development synthetic reversal run reports E_rb−RMM mean ΔJ −6.65, 95% t CI [−7.31, −6.00] across three regimes/four hosts. The ablation is decisive for attribution: `h_min` horizon gate never binds; `alpha_rb=.05` instead of .10 loses roughly 4–6 cost units; start-grid is also material. A valid next comparison therefore matches rollback alpha and start grid and includes a standard two-sided SR/CUSUM detector. Existing evidence does not support the added cost-to-go gate as the repair mechanism.

On real reversal episodes (16 / 7 sources), four host contrasts are wide and only two intervals exclude zero. Episodes are retrospective classifications and exposed, so the result is descriptive transfer evidence only.

## Cost decomposition and test requirements

The existing simulator records predictive loss, requested label count, deployment switches and net cost (`scripts/promising_directions/sota/simulator.py`). A confirmatory comparison must report these separately, with identical pathwise budget, horizon, release delays, label price, switch cost and information. For null controls, name the tested conditional/marginal/economic null; report the error rate and uncertainty only for correctly specified nulls. Report adverse early, transient, persistent, no-benefit and reversal regimes even when unfavorable.

No fresh ablation was run here. The above synthesis preserves reported results and explicitly distinguishes them from a new confirmatory evaluation.

## Corrected Sprint 2 replay amendment

The corrected 100-seed synthetic replay provides a more direct pacing contrast. In `V_late_600` and `W_late_1000`, Gated+front and ordinary Gated have nearly identical cost (front−Gated −0.06 [−0.54,+0.43] and −0.24 [−0.56,+0.08]); front-loading alone does not explain C2/C6's 7.4–7.8 J reduction versus front in those two selected regimes. C2/C6 promotion rates remain at or below 1% in these cells, so the improvement reflects lower expenditure under absent/rare promotion rather than demonstrated faster promotion. Across other alternative regimes C2/C6 are often worse than front, and on reversal they lose to ordinary Gated by about 38 J in `W_reversal_700`.

Across both corrected source cohorts, front-loading versus ordinary Gated averages −24.55 J per source (t95 [−42.81,−6.29], 14 exposed sources); front versus tuned pacing is −0.30 [−1.05,+0.45], and C2/C6 versus front are statistically unresolved at source level. In the five-source cohort alone, front−Gated is −46.12 [−100.12,+7.87]. Exposure, related domains, dependent episodes and proxy feedback chronology preclude a mechanism transfer claim. C2/C6 behavior is also prior-developed and exposes high false-promotion rates under the out-of-class marginal-null stresses (`O_null_order2`: .216/.208 vs .031 Gated; `O_null_semimarkov`: .140/.126 vs .062). These stress rates do not refute a theorem outside its null class, but they limit any broad robustness claim.

All row-level summaries, corrected null-class distinctions, provenance hashes and limitations are in `CORRECTED_REPLAY_AUDIT.md`. No new method ablation was conducted, and these correction replays are not confirmation.
