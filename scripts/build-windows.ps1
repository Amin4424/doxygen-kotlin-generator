# Windows Build Script for Kotlin Doxygen Filter

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "=== Kotlin Doxygen Build Script (Windows) ===" -ForegroundColor Green

# 1. Setup Virtual Environment if not exists
$VenvDir = Join-Path $ProjectRoot "venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$PyInstallerExe = Join-Path $VenvDir "Scripts\pyinstaller.exe"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment in 'venv'..." -ForegroundColor Cyan
    python -m venv venv
}

# 2. Upgrade pip and install development dependencies
Write-Host "Installing/updating dependencies in virtual environment..." -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip
& $PipExe install -e .[dev]

# 3. Run tests
Write-Host "Running tests..." -ForegroundColor Cyan
& $PythonExe -m unittest discover -s tests

# 4. Build executable using PyInstaller
Write-Host "Building standalone executable using PyInstaller..." -ForegroundColor Cyan
& $PyInstallerExe --onefile --clean --name kotlin-doxygen kotlin_doxygen\__main__.py

# 5. Verify and output
$ExePath = Join-Path $ProjectRoot "dist\kotlin-doxygen.exe"
if (Test-Path $ExePath) {
    Write-Host "`nSuccess! Executable successfully generated at:" -ForegroundColor Green
    Write-Host "$ExePath" -ForegroundColor Yellow
} else {
    Write-Error "Build failed: Executable not found at $ExePath"
}
