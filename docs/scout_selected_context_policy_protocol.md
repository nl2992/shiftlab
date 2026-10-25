# Target-scout selection with a fresh certification slice

**Status:** frozen 2026-10-24 before execution. This is an exploratory
synthetic development screen, not calibration or real-world confirmation.

## Motivation and question

The source-validation composite policy performed poorly in a disjoint-seed
replication. Its evaluator-known target-monitor mean gain was negative at latent
context prevalences 0.10 and 0.50, and positive only in the 0.90 / strongest-
signal cells. This motivates a sample-split policy selector that sees a short
target-period scout before the certification monitor begins. The question is
whether that target-informed candidate choice can improve future decision value
enough to offset spending half of the monitor horizon on selection.

## Frozen two-stage rule

Keep the fitted 13-candidate family, train/validation data, target DGP, proxy,
query policy, global bound, and hard caps unchanged. Split the existing monitor
horizon at its midpoint:

1. **Scout:** query under the registered uniform propensity and use the first
   half of the target monitor to estimate each candidate's context-specific
   paired gain. For candidate `k` and visible context `g`, use the direct-IPW
   mean
   `sum_{t in scout, C_t=g} I_t Delta_{k,t}/q_t / N_g`, where `N_g` is the
   number of learner-visible scout events in that context. Select the estimated
   best candidate for each context only if its estimated gain exceeds the
   exposure-prorated switch charge `c_switch/H`; otherwise select the incumbent
   there. The scout labels select the policy and are not reused by its test.
2. **Certification:** freeze the selected context-to-candidate map at the
   midpoint, then apply one fixed-stake direct-IPW e-process at the full alpha
   to the second half of the monitor. A fallback context contributes zero. The
   tested null is the overall history-conditional mean net gain of this fixed
   policy, integrated over incoming contexts; this does not provide a separate
   safety guarantee in each context. If the hard label cap is exhausted during
   scouting, no certification or promotion occurs.

Selection is outcome-adaptive within the scout, but the tested policy is fixed
before certification. Under the registered iid target stream, predictable
positive query propensities, bounded increments, and the stated aggregate
conditional-mean null, the certification e-process retains its usual validity
conditional on the scout history. This argument does not cover arbitrary
serial dependence, delayed or selectively available labels, adaptive context
definitions, or action-dependent outcomes. It is sample splitting plus an
established e-process, not a novelty claim.

## Frozen factorial and analysis

- `n=3,200`, `d=16`, 30 matched seeds per cell, seed IDs
  `20261130`–`20261159`, disjoint from both previous context-policy screens.
- Latent context prevalence 0.10/0.50/0.90, signal displacement 0/0.05/0.10,
  and proxy error 0/0.10/0.25.
- Uniform direct-IPW queries, fixed-mixture certification, alpha 0.05, and
  shared 20%/40% realized label caps across scout and certification.
- Compare the target-scout policy with pooled-rank, nested-equal,
  nested-volume, and source-validation-selected policies on the same generated
  streams and query uniforms. Primary outcome: evaluator-known cumulative
  future net decision-cost gain at the 40% cap.
- Primary contrasts: target-scout minus pooled-rank and target-scout minus
  nested-volume, equally averaging the 18 positive-signal prevalence/error
  cells. Use paired seed-block bootstrap intervals at 97.5% per contrast.
- Proceed to independent calibration only if both lower confidence limits exceed
  the registered +1 cumulative-utility margin and the zero-signal controls show
  no material escalation signal. Otherwise retire this rule.

The development intervals are conditional on this simulator and the stated
assumptions. Do not pool with prior screens. No figure is planned; any figure
must use PaperBanana.

## Reproduction

```powershell
uv run shiftlab-dive-budgeted-context-grid scout-develop `
  --seeds 30 --seed-offset 20261130 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_selected_context_policy_protocol.md `
  --output outputs/scout_selected_context_policy_30
```
