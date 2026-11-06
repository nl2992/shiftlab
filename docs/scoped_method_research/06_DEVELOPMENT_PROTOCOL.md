# Rollback/acquisition pilot protocol

Protocol frozen before reading the new pilot summaries: 2026-11-06.

## Scope and information boundary

This is a bounded development-only audit. It uses three existing synthetic regimes with evaluator
truth available to the simulator and only 30 paired seeds per regime. No real data, holdout data, or
confirmation outcomes are read. The screen runner replays the same generated loss episode across
all policies for each seed. Policy and label-stream randomization use the runner's paired stream
construction.

## Fixed experiment contract

- Regimes: `F3_reversal_800`, `S_reversal_400`, `F4_recurrent`.
- Paired seed count: 30 per regime; base seed `2026110617`.
- Runner: `scripts/sota_sprint/screen.py` at the current worktree HEAD; 4 workers.
- Shared contract: repository `bench.CONTRACT`, T=2000, B=200, query cost `c_q=0.05`, switch cost
  `c_s=5`, nominal alpha=0.05; each regime's registered label delay is used unchanged.
- Policies: `E_rb:gated_deployment`, `E_rb:gated_deployment-a05`, `E_srr:gated_deployment`,
  `E_srrSR:gated_deployment`, `E_srr_noacq:gated_deployment`, `B0_host`, `B2`, `B5`,
  `gated_deployment`, `CONTROL_never_switch`.
- Primary descriptive outcome: per-episode net deployment cost. Secondary traces: predictive loss,
  label count, switches, promotions, rollbacks, first promotion time, wrong-model exposure, labels
  before event 500/after event 1000, and budget exhaustion time (as recorded by screen.py).
- Contrasts are paired within regime and seed. Report mean difference with a 95% paired t interval;
  also show per-regime effects to avoid pooling the three regimes as if they were sampled source
  clusters. These intervals describe this development sample and are not confirmatory.

## Comparators and interpretation

- E_rb vs `E_rb-a05` changes only rollback alpha within the same wrapper.
- E_rb vs `E_srr`/`E_srrSR` changes the detector family while retaining the host/acquisition
  scaffold. SRR has its documented average-run-length interpretation, not the RMM anytime guarantee.
- `E_srr_noacq` is a coarse post-promotion acquisition ablation and simultaneously uses SRR/CUSUM;
  it is not interpreted as a pure acquisition effect.
- B0/B2/B5 separate the no-rollback RMM wrapper, rollback, and reserve+rollback+deadline, but B5
  changes multiple components. The repository's existing Family B ablations are needed for causal
  attribution of reserve vs deadline.
- `gated_deployment` and never-switch provide base and action-floor references. None is presumed to
  be the strongest published comparator for a paper claim.

## Exact command

```sh
uv run python scripts/sota_sprint/screen.py --regimes F3_reversal_800,S_reversal_400,F4_recurrent --policies E_rb:gated_deployment,E_rb:gated_deployment-a05,E_srr:gated_deployment,E_srrSR:gated_deployment,E_srr_noacq:gated_deployment,B0_host,B2,B5,gated_deployment,CONTROL_never_switch --seeds 30 --seed-base 2026110617 --workers 4 --out research/scoped_method/pilots/rollback_acquisition_30seed_20261106
```

Outputs are local development records under that isolated pilot directory. They contain policy
metrics/traces from synthetic episodes, no raw real-world data. Do not reuse this seed set as
confirmation or select a new method from the output and call it confirmatory.
