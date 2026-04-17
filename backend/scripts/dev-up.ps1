param(
    [string]$PythonVersion = "3.11",
    [string]$Host = "0.0.0.0",
    [int]$Port = 8001,
    [switch]$SkipInstall,
    [switch]$NoReload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Resolve-BackendRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function New-VenvIfNeeded {
    param(
        [string]$BackendRoot,
        [string]$PyVersion
    )

    $venvPython = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Host "Virtual environment already exists: .venv"
        return $venvPython
    }

    Write-Step "Creating virtual environment (.venv)"
    try {
        & py "-$PyVersion" -m venv (Join-Path $BackendRoot ".venv")
    } catch {
        Write-Host "py launcher failed, fallback to current python..." -ForegroundColor Yellow
        & python -m venv (Join-Path $BackendRoot ".venv")
    }

    if (-not (Test-Path $venvPython)) {
        throw "Failed to create .venv. Please check Python installation."
    }

    return $venvPython
}

function Ensure-EnvFile {
    param([string]$BackendRoot)

    $envPath = Join-Path $BackendRoot ".env"
    if (Test-Path $envPath) {
        Write-Host ".env exists."
        return
    }

    $examplePath = Join-Path $BackendRoot ".env.example"
    if (-not (Test-Path $examplePath)) {
        throw ".env.example not found."
    }

    Copy-Item $examplePath $envPath
    Write-Host "Created .env from .env.example"
    Write-Host "Please verify your DB config in backend/.env before continuing." -ForegroundColor Yellow
}

$backendRoot = Resolve-BackendRoot
Set-Location $backendRoot

Write-Step "Backend root: $backendRoot"
$pythonExe = New-VenvIfNeeded -BackendRoot $backendRoot -PyVersion $PythonVersion

if (-not $SkipInstall) {
    Write-Step "Installing dependencies"
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r (Join-Path $backendRoot "requirements.txt")
} else {
    Write-Host "Skip dependency installation."
}

Write-Step "Ensuring .env exists"
Ensure-EnvFile -BackendRoot $backendRoot

Write-Step "Running database migrations"
$alembicExe = Join-Path $backendRoot ".venv\Scripts\alembic.exe"
if (-not (Test-Path $alembicExe)) {
    throw "alembic executable not found: $alembicExe"
}
& $alembicExe upgrade head

Write-Step "Starting server"
$uvicornArgs = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", $Host,
    "--port", "$Port"
)
if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

Write-Host "Running: python $($uvicornArgs -join ' ')" -ForegroundColor DarkGray
& $pythonExe @uvicornArgs
