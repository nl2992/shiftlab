# Detached Stage-B tranche-2 scope (iii) (Q1 evidence identities, A1) with a restart watchdog (the ledger is the checkpoint).
param([string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)), [int]$Workers = 12)
$py = Join-Path (Split-Path -Parent $Root) "shift-research-starter/.venv/Scripts/python.exe"
$env:PYTHONPATH = "$Root/src"
$log = "$Root/results/d2a_rar/stage_b/stage_b_t2_iii_run.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
for ($i = 1; $i -le 5; $i++) {
    "=== attempt $i $(Get-Date -Format s) ===" | Out-File -Append -Encoding utf8 $log
    & $py "$Root/scripts/d2a_rar/run_stage_b_t2.py" --scope-iii --run --workers $Workers *>> $log
    if ($LASTEXITCODE -eq 0) { "=== finished OK $(Get-Date -Format s) ===" | Out-File -Append -Encoding utf8 $log; break }
    Start-Sleep -Seconds 20
}
