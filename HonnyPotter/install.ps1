# HonnyPotter Installation Script for HoneyBee (Windows PowerShell)
# 
# This script sets up HonnyPotter as a standalone honeypot on Windows.

param(
    [string]$PotID = $env:HONEYBEE_POT_ID,
    [string]$InstallDir = $PSScriptRoot
)

if ([string]::IsNullOrEmpty($PotID)) {
    $PotID = "honnypotter-01"
}

$LogDir = Join-Path $InstallDir "logs"

Write-Host "🍯 Installing HonnyPotter for HoneyBee..." -ForegroundColor Cyan
Write-Host "   Pot ID: $PotID"
Write-Host "   Install Directory: $InstallDir"
Write-Host ""

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Write-Host "✅ HonnyPotter installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "   Pot ID: $PotID"
Write-Host "   Log File: $(Join-Path $LogDir 'honnypotter.log')"
Write-Host "   HoneyBee Forwarder: Enabled"
Write-Host ""
Write-Host "To start:" -ForegroundColor Yellow
Write-Host "   1. Configure your web server to point to: $(Join-Path $InstallDir 'standalone.php')"
Write-Host "   2. Or use as WordPress plugin: Copy to wp-content\plugins\HonnyPotter\"
Write-Host "   3. Set HONEYBEE_POT_ID environment variable if different from default"
Write-Host ""
Write-Host "Testing:" -ForegroundColor Yellow
Write-Host "   Invoke-WebRequest -Uri http://localhost/standalone.php -Method POST -Body @{log='admin';pwd='password123'}"

