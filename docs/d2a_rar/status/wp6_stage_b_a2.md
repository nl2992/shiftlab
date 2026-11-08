# WP6 Stage B amendment A2 status (placeholder; replaced by the generated report when the arms finish)

State when written: both arms were launched detached and were still warming comparator reference runs. No A2 ledger record
existed yet. G0 (RAR arm, host-only reference check) had not been computed.

## Check progress

Logs are UTF-16 (PowerShell `Out-File`); read with `Get-Content <file> -Encoding Unicode -Tail 40`:

- Q1 arm: `results/d2a_rar/stage_b/stage_b_a2_q1_run.log`
- RAR arm: `results/d2a_rar/stage_b/stage_b_a2_rar_run.log`
- Progress state (shared by both arms, last writer wins): `results/d2a_rar/stage_b/a2_state.json`
- Reference cache files written: `ls results/d2a_rar/stage_b/cache/a2__* | wc -l` (about 1,200 expected in total)
- Per-experiment worker output: `results/d2a_rar/stage_b/work_a2/`
- Decided records: `python -c "from shiftlab.autoresearch import ledger; r=[x for x in ledger.read_all() if x.get('suite')=='a2']; print([(x['candidate_key'],x['decision']) for x in r])"` (with `PYTHONPATH=src`)

## G0 output

`results/d2a_rar/stage_b/a2_g0.json` is written by the RAR arm after its references finish and before any candidate runs.
If `"pass": false`, no K2/K1/L record is written and the arm is UNVERIFIED (the phase in `a2_state.json` says
"G0 FAILED"). It is computed from cached host and NoCanary reference runs only and writes no ledger record. Canary entry is
proxied by N_r >= 1.

## Write the final status

```
cd shiftlab-d2a-rar-2026-11-07
set PYTHONPATH=src
<venv>/Scripts/python.exe -m shiftlab.autoresearch.stage_b_a2 --status
```

This overwrites this file with the generated report (numbers copied from the ledger records: both readings, paired dJ CIs,
Clopper-Pearson upper bounds, and the 100-replicate null audit). Verify the ledger chain with
`python -c "from shiftlab.autoresearch import ledger; print(ledger.verify())"`.

## Restart the watchdog

The ledger is the checkpoint: decided keys are skipped and cached references are reused, so restarts are safe. Launch each arm
with at most 6 workers while both run (12 in total):

```
powershell -File scripts/d2a_rar/run_stage_b_a2_watchdog.ps1 -Arm q1  -Workers 6
powershell -File scripts/d2a_rar/run_stage_b_a2_watchdog.ps1 -Arm rar -Workers 6
```

To stop: end the python processes whose command line contains `stage_b_a2`.

## Tests

The full `tests/d2a_rar` run (started in the background) had not finished when this was written: about 52% passed with no
failures at the last check. `tests/d2a_rar/test_a2.py`: 9 passed. Ruff is clean on the new files. Re-run
`python -m pytest tests/d2a_rar -q` for the summary line.
