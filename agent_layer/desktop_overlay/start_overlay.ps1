param(
  [string]$Student = "S01",
  [ValidateSet("gaokao_registration","score_improvement")]
  [string]$Scenario = "gaokao_registration"
)
$ErrorActionPreference = 'Stop'
$overlay = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $overlay "tender_overlay.py"
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
Start-Process -FilePath $pythonw -ArgumentList @($script, "--student", $Student, "--scenario", $Scenario) -WorkingDirectory $overlay -WindowStyle Hidden
Write-Output "Tender desktop overlay started for $Student / $Scenario"
