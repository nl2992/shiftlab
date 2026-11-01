# Detached, resumable launcher for the Failure Atlas cycle-6 validity run (Amendment 7).
# Re-running it resumes from outputs/failure_atlas_v1_cycle6/configs.jsonl.
param([int]$Workers = 10)
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root "outputs\failure_atlas_v1_cycle6"
New-Item -ItemType Directory -Force $out | Out-Null
$py = Join-Path $root ".venv\Scripts\python.exe"
$script = Join-Path $root "scripts\run_atlas_cycle6_validity_v1.py"
$p = Start-Process -FilePath $py `
    -ArgumentList @("`"$script`"", "--workers", $Workers, "--out", "`"$out`"") `
    -WorkingDirectory $root -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $out "run.log") `
    -RedirectStandardError (Join-Path $out "run.err") -PassThru
$p.Id | Out-File -Encoding ascii (Join-Path $out "run.pid")
Write-Output "started pid $($p.Id)"
