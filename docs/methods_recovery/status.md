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
