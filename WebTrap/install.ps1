# WebTrap installation script for HoneyBee (Windows PowerShell).
$ErrorActionPreference = "Stop"

$PotId = if ($env:HONEYBEE_POT_ID) { $env:HONEYBEE_POT_ID } else { "webtrap-01" }
$InstallDir = if ($args.Count -ge 1) { $args[0] } else { (Get-Location).Path }
$LogDir = Join-Path $InstallDir "logs"
$UploadDir = Join-Path $InstallDir "captured_uploads"

Write-Host "🍯 Installing WebTrap for HoneyBee..."
Write-Host "   Pot ID:            $PotId"
Write-Host "   Install Directory: $InstallDir"
Write-Host ""

New-Item -ItemType Directory -Force -Path $LogDir    | Out-Null
New-Item -ItemType Directory -Force -Path $UploadDir | Out-Null

$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3 is required but '$python' was not found in PATH."
    exit 1
}

$venv = Join-Path $InstallDir "venv"
if (-not (Test-Path $venv)) {
    Write-Host "📦 Creating virtualenv..."
    & $python -m venv $venv
}

$pip = Join-Path $venv "Scripts\pip.exe"
& $pip install --quiet --upgrade pip
& $pip install --quiet -r (Join-Path $InstallDir "requirements.txt")

$envFile = @"
HONEYBEE_POT_ID=$PotId
HONEYBEE_HOST=$($env:HONEYBEE_HOST ?? "127.0.0.1")
HONEYBEE_PORT=$($env:HONEYBEE_PORT ?? "9100")
HONEYBEE_ENABLE=$($env:HONEYBEE_ENABLE ?? "true")
HONEYBEE_ENABLE_FILE_LOG=true
HONEYBEE_LOG_FILE=$LogDir\webtrap.log
WEBTRAP_BIND_HOST=$($env:WEBTRAP_BIND_HOST ?? "0.0.0.0")
WEBTRAP_BIND_PORT=$($env:WEBTRAP_BIND_PORT ?? "8088")
"@
Set-Content -Path (Join-Path $InstallDir ".env") -Value $envFile -Encoding utf8

Write-Host "✅ WebTrap installed successfully"
Write-Host ""
Write-Host "Start it with:"
Write-Host "   cd $InstallDir; .\venv\Scripts\Activate.ps1; python standalone.py"
