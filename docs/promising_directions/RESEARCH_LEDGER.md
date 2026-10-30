# Research ledger (append-only)

One line per cycle event, written by `scripts/promising_directions/research_loop.py`. Do not edit
earlier lines.

- 2026-10-30T17:52:43+00:00 cycle-0001-C0-smoke task=C0-smoke outcome=completed error=None
- 2026-10-30T17:52:43+00:00 session end stop_reason=queue_empty next=None
- 2026-10-30T17:52:44+00:00 session end stop_reason=queue_empty next=None
- 2026-10-30 A1-exact-separation (lane A) executed by subagent outside loop scheduler under registered protocol 0d03912; outputs docs/promising_directions/results/a1 (summary sha256 5e121765c7550b9aff813bbc8c339e0cecda5b546ad6a85465126d3fe237a2b5); verified by orchestrator recomputation; decision KILL (max rel gap 0.8741%)
- 2026-10-30 B1-certified-switching (lane B) executed by subagent under registered protocol 1a742dc; outputs docs/promising_directions/results/b1 (summary sha256 0062aec5eeba38caf93cdc69d307c9b957928ba0450b9911447566fc010a562e); orchestrator recomputed world-averaged costs/CIs from per_seed.npz; Q1 MIXED (max 3.5% vs 10% target), Q2 NOT SUPPORTED, validity OK (0/500 false promotions)
- 2026-10-30 B2-propensity-cap (lane B) executed by subagent under registered protocol af14d5a, fresh seeds 20261101; outputs docs/promising_directions/results/b2 (summary sha256 4af87b4fad2d9ca2ac5cfe32616728ba1fea0f0a3d98db06d38cbede2441b488); orchestrator recomputed; Q1 MIXED (P3b -10.2/-9.65/-7.9/-7.7% vs BEST; W3 reversal +14.3% at B400 cs20); validity OK; B1 default path bit-identical. No confirmation authorised.
