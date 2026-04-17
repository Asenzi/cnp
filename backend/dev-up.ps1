param(
    [string]$PythonVersion = "3.11",
    [string]$Host = "0.0.0.0",
    [int]$Port = 8001,
    [switch]$SkipInstall,
    [switch]$NoReload
)

$scriptPath = Join-Path $PSScriptRoot "scripts\dev-up.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Script not found: $scriptPath"
}

& $scriptPath `
    -PythonVersion $PythonVersion `
    -Host $Host `
    -Port $Port `
    -SkipInstall:$SkipInstall `
    -NoReload:$NoReload
