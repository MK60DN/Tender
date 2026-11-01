param()
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$script = Join-Path $PSScriptRoot 'media_plugins_mcp.py'
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
if (-not $python) {
  [Console]::Error.WriteLine('Tender Media Tools: Python with media dependencies was not found. Set TENDER_PYTHON.')
  exit 2
}
& $python $script
exit $LASTEXITCODE
