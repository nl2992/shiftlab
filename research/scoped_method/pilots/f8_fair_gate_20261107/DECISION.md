# Fair validation-gate pilot decision

## Result

The one-look in-horizon validation gate did not preserve the known fixed-challenger advantage on
the registered F8 primary cell. Across 50 fresh paired streams, its net cost was 226.439 versus
211.482 for CAMS (`fair_validation_gate - cams_adapter = +14.957`, paired percentile-bootstrap 95%
CI `[+11.379,+18.703]`). The frozen criterion required at least 5 units saved with an interval
below zero; it failed in the opposite direction. The gate also cost 4.335 more than
SMCS+retain-incumbent (CI `[+1.114,+7.766]`) and was unresolved against gated deployment
(`-3.269`, CI `[-6.602,+0.386]`).

The breakdown on F8 was mean predictive loss 222.120, 12.38 labels (0.619 label cost), and 0.74
switches (3.700 switch cost). The gate promoted 37/50 times, always at event 500. CAMS cost 211.482
(204.960 loss, 30.44 labels / 1.522 label cost, one switch / 5.000 switch cost). The
known-in-advance `fixed_challenger` upper control cost 205.500, but it is not an implementable
competitor because its identity is supplied without paying for selection. It was 20.939 cheaper
than the in-horizon gate (paired CI `[+17.676,+24.378]`).

Adverse cells show the boundary. In `F0_null`, the gate promoted once in 50 streams (2%), spent
80.4 labels on average, and cost 4.300 more than never-switch (paired CI `[+3.932,+4.942]`). In
`F3_reversal_800`, it promoted 44/50 times and cost 71.616 more than never-switch (CI
`[+62.860,+79.744]`) and 58.932 more than gated deployment (CI `[+49.369,+67.828]`). This gate has
no post-promotion rollback and is not proposed for those environments.

## Decision

**BENCHMARK_ONLY.** This falsification pilot does not identify a distinct repair or practical
headroom for an implementable fixed-challenger validation gate. The earlier positive F8 fixed-policy
result is explained by supplying the target model identity in advance; charging a realistic shared
validation horizon removes the advantage against CAMS. This result is limited to the specified
synthetic regimes, policy adapters and operating contract. It does not establish that every possible
deployment rule or environment lacks economic headroom. No independent real-data confirmation of a
new repair is warranted, and no new method should be added from this pilot.

## Fidelity and limitations

- All policies use the same generated paired loss stream, 2,000-event horizon, label cost 0.05,
  switch cost 5, and pathwise budget cap 200. The candidate makes one decision only after its 400-event
  validation window and 100-event label delay; its training/selection cost is otherwise not modeled.
- CAMS uses the repository's constant-policy adapter. SMCS is the repository's explicitly named
  `SMCS+retain-incumbent` deployment adapter. Gated Deployment uses the repository's gated-deployment
  certificate adapter. They are compared with their stored implementations, not reimplemented here.
- The one-sided Clopper-Pearson decision is a conventional single-look gate. Its binomial
  interpretation applies to iid queried disagreement signs in the stationary F8 construction; the
  null and reversal rows are adverse economic diagnostics, not a guarantee evaluation.
- The experiment uses synthetic paired model-loss streams, not independently trained models. It
  does not include RMM/E_rb or conventional SR/CUSUM in this follow-up; those were covered in the
  registered economic-headroom and rollback pilots, whose negative results remain controlling for
  those candidate families.
- Percentile intervals resample the 50 paired episode seeds; they quantify Monte Carlo variation
  under this simulator, not source-level real-world uncertainty.

## Artifacts and reproduction

- Frozen protocol: `PROTOCOL.md`.
- Exact policy and runner: repository files `scripts/failure_atlas_v2_flq/fair_validation_gate.py`,
  `f8_fair_extra.py`, and `run_atlas_v2.py`.
- Raw paired records: `run/records.jsonl`; run configuration and timing: `run/manifest.json`.
- Machine-readable summaries: `RESULTS.json`; paired bootstrap code: `analyze.py`.
- Reproduce from the repository root with the command in `PROTOCOL.md`, then run
  `uv run python research/scoped_method/pilots/f8_fair_gate_20261107/analyze.py`.

## Smallest next action

Stop candidate expansion. If this line is used in a paper, report F8 as a benchmark contrast between
a known fixed-policy upper control and an implementable paid validation gate, together with its null
and reversal failures and the earlier EIA replay limitations.
