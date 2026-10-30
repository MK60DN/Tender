$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
try {
    python -m uvicorn app.main:app --reload --port 8080
}
finally {
    Pop-Location
}
