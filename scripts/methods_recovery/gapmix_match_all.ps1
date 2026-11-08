$w = 'C:\Users\nigel\OneDrive\桌面\ICML\shiftlab-methods-recovery-2026-11-07'
Set-Location $w
$env:PYTHONPATH = "$w\src"; $env:OPENBLAS_NUM_THREADS = "1"; $env:OMP_NUM_THREADS = "1"
$py = 'C:\Users\nigel\OneDrive\桌面\ICML\shift-research-starter\.venv\Scripts\python.exe'
function WaitMem { for ($i = 0; $i -lt 90; $i++) { if ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory -ge 1572864) { return }; Start-Sleep 120 } }
$steps = @(
  @('null','0.8'), @('alt','0.95'), @('null','0.95')
)
foreach ($st in $steps) {
  for ($try = 0; $try -lt 5; $try++) {
    WaitMem
    & $py scripts/methods_recovery/gapmix_match.py run --kind $st[0] --workers 4 --max-rho $st[1] *>> "outputs/methods_recovery/gapmix_match/run_$($st[0]).log"
    if ($LASTEXITCODE -eq 0) { break }
  }
}
& $py scripts/methods_recovery/gapmix_match.py summarize *>> "outputs/methods_recovery/gapmix_match/run_summ.log"
'DONE' | Out-File outputs/methods_recovery/gapmix_match/DONE.txt
