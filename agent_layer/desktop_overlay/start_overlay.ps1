param(
  [string]$Student = "S01",
  [ValidateSet("gaokao_registration","score_improvement")]
  [string]$Scenario = "gaokao_registration"
)
$ErrorActionPreference = 'Stop'
$overlay = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $overlay "tender_overlay.py"
$candidates = @()
if ($env:TENDER_PYTHON) { $candidates += $env:TENDER_PYTHON }
$candidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
$candidates += 'C:\Python312\python.exe'
$candidates += 'C:\Python311\python.exe'
$python = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $python) {
  $command = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($command -and $command.Source -notmatch 'WindowsApps') { $python = $command.Source }
}
if (-not $python) { throw 'Python was not found. Set TENDER_PYTHON to a Python 3.11+ interpreter.' }
$pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { $pythonw = $python }
Start-Process -FilePath $pythonw -ArgumentList @($script, "--student", $Student, "--scenario", $Scenario) -WorkingDirectory $overlay -WindowStyle Hidden
Write-Output "Tender desktop overlay started for $Student / $Scenario"
