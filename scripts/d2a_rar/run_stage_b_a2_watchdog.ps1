# Detached Stage-B amendment A2 arm (q1 | rar) with a restart watchdog (the ledger is the checkpoint; decided keys are skipped).
param([string]$Arm = "q1", [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)), [int]$Workers = 12)
$py = Join-Path (Split-Path -Parent $Root) "shift-research-starter/.venv/Scripts/python.exe"
$env:PYTHONPATH = "$Root/src"
$log = "$Root/results/d2a_rar/stage_b/stage_b_a2_${Arm}_run.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
for ($i = 1; $i -le 5; $i++) {
    "=== attempt $i $(Get-Date -Format s) ===" | Out-File -Append -Encoding utf8 $log
    & $py -m shiftlab.autoresearch.stage_b_a2 "--$Arm" $Workers *>> $log
    if ($LASTEXITCODE -eq 0) { "=== finished OK $(Get-Date -Format s) ===" | Out-File -Append -Encoding utf8 $log; break }
    Start-Sleep -Seconds 20
}
