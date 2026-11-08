# Gap-Mix+ status log (methods-recovery, branch research/methods-recovery-2026-11-07)

- [x] Step 1a: src/shiftlab/gaver/gapmix_plus.py written (governor, 4a via mode=frozen, Arm 5 via mode=pace, QSG-envelope evidence port). Smoke test pending.
- [ ] Step 1b: runner scripts/methods_recovery/run_gmplus.py
- [ ] Step 2: tests/gaver/test_gapmix_plus.py + ruff
- [ ] Step 3: seed registry
- [ ] Step 4: tuning -> configs/methods_recovery/gapmix_plus_frozen.json, 10_TUNING.md
- [ ] Step 5: eval (detached)
- [ ] Step 6: 20_GAPMIX_PLUS_RESULTS.md

- 2026-11-07T22:29:10 steps 1-3 done (module, tests 8 passed + ruff clean, seeds registered 101300000-309999 tuning, 101400000-429999 eval). Tuning launched detached: outputs/methods_recovery/tune/rows.csv (resumable: rerun same command: run_gmplus.py --stage tune --workers 10). Arm4 grid shifted to kappa{1,2,4} x phi{1,1.5,2.5} x omega{0,.5,1} after an 8-cell/1-seed smoke on tuning seeds (kappa=2,phi=1.5 at old grid edge); 27 configs. Arm5 32 configs.
- 22:33:35 analysis scripts written: scripts/methods_recovery/{tune_select,analyse_gmplus}.py. Tuning ~110 min est (23040 runs).
- 23:38:01 tuning DONE; frozen config + sha256 written (configs/methods_recovery/gapmix_plus_frozen.json), 10_TUNING.md written. Launching eval: alt then null, detached (outputs/methods_recovery/eval.log). Resume: rerun run_gmplus.py --stage alt / --stage null --workers 10.

## 2026-11-07 23:45 (Opus coordinator)
- Verified: frozen config sha256 1010a0f9… written 23:37:51, first eval row 23:38:05 (freeze precedes eval). 15 tests pass. Committed 9edca5e1.
- Eval running detached (parent shell gone): alt stage about 80 min, then null stage about 2 h. The agent was stopped; the run is unaffected.
- NEXT: when both stages print "done" in outputs/methods_recovery/*/eval.log, run `scripts/methods_recovery/analyse_gmplus.py`. Opus then checks that the C3 numbers do NOT use the per-cell-table fallback (Arm 3 -> Arm 2 values when PAVE rows are absent; it applies outside the delay gate, where delay-gated PAVE = shell rule). Recompute criteria 1-5 and commit the verdict.
- Watch: tuning gain for Arm 4 over Arm 2 was only 0.75% (0.4386 vs 0.4419), against a >=3% C3 bar. kappa=4 sits on the grid edge; omega=0 means the pending-label term is unused.
