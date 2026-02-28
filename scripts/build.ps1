# Tether Build Script
# Usage: .\scripts\build.ps1

param(
    [switch]$SkipPython = $false,
    [switch]$SkipTauri = $false
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tether Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Build Python Runtime
if (-not $SkipPython) {
    Write-Host "`n[1/4] Building Python runtime with uv..." -ForegroundColor Yellow

    $PythonRuntimeDir = Join-Path $ProjectRoot "python-runtime"
    $VenvDir = Join-Path $ProjectRoot ".venv-build"

    # Remove existing runtime if present
    if (Test-Path $PythonRuntimeDir) {
        Write-Host "Removing existing python-runtime..." -ForegroundColor Gray
        Remove-Item -Recurse -Force $PythonRuntimeDir
    }
    if (Test-Path $VenvDir) {
        Write-Host "Removing existing build venv..." -ForegroundColor Gray
        Remove-Item -Recurse -Force $VenvDir
    }

    # Create virtual environment
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    uv venv $VenvDir

    # Install dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Gray
    uv pip install --python $VenvDir\Scripts\python.exe sounddevice faster-whisper httpx

    # Create portable runtime (copy venv)
    Write-Host "Creating portable runtime..." -ForegroundColor Gray
    Copy-Item -Path $VenvDir -Destination $PythonRuntimeDir -Recurse

    # Clean up build venv
    Remove-Item -Recurse -Force $VenvDir

    Write-Host "Python runtime created at: $PythonRuntimeDir" -ForegroundColor Green
}

# Step 2: Copy engine folder to bundle location
Write-Host "`n[2/4] Copying engine to bundle..." -ForegroundColor Yellow

$BundleEngineDir = Join-Path $ProjectRoot "src-tauri\engine"
if (Test-Path $BundleEngineDir) {
    Remove-Item -Recurse -Force $BundleEngineDir
}
Copy-Item -Path (Join-Path $ProjectRoot "engine") -Destination $BundleEngineDir -Recurse
Write-Host "Engine copied to: $BundleEngineDir" -ForegroundColor Green

# Step 2b: Copy python-runtime to src-tauri for bundling (needed during tauri build)
Write-Host "`n[2b/4] Copying python-runtime for bundling..." -ForegroundColor Yellow
$BundlePythonDir = Join-Path $ProjectRoot "src-tauri\python-runtime"
if (Test-Path $BundlePythonDir) {
    Remove-Item -Recurse -Force $BundlePythonDir
}
Copy-Item -Path (Join-Path $ProjectRoot "python-runtime") -Destination $BundlePythonDir -Recurse
Write-Host "Python runtime copied to: $BundlePythonDir" -ForegroundColor Green

# Step 3: Build Tauri App
if (-not $SkipTauri) {
    Write-Host "`n[3/4] Building Tauri application..." -ForegroundColor Yellow

    # Ensure npm dependencies are installed
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm dependencies..." -ForegroundColor Gray
        npm install
    }

    # Build frontend first
    Write-Host "Building frontend..." -ForegroundColor Gray
    npm run build

    # Build Tauri
    Write-Host "Building Tauri..." -ForegroundColor Gray
    npm run tauri build

    Write-Host "Tauri build complete!" -ForegroundColor Green
}

# Step 4: Verify Build
Write-Host "`n[4/4] Verifying build..." -ForegroundColor Yellow

$ExePath = Join-Path $ProjectRoot "src-tauri\target\release\tether.exe"
if (Test-Path $ExePath) {
    $ExeSize = (Get-Item $ExePath).Length / 1MB
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable: $ExePath" -ForegroundColor Green
    Write-Host "Size: $([math]::Round($ExeSize, 2)) MB" -ForegroundColor Green
} else {
    Write-Host "ERROR: Executable not found at $ExePath" -ForegroundColor Red
    exit 1
}

# Step 5: Bundle Python runtime and engine with release
Write-Host "`n[5/5] Bundling Python runtime and engine..." -ForegroundColor Yellow

$ReleaseDir = Join-Path $ProjectRoot "src-tauri\target\release"

# Copy Python runtime
$PythonRuntimeSrc = Join-Path $ProjectRoot "python-runtime"
$PythonRuntimeDst = Join-Path $ReleaseDir "python-runtime"
if (Test-Path $PythonRuntimeDst) {
    Remove-Item -Recurse -Force $PythonRuntimeDst
}
Copy-Item -Path $PythonRuntimeSrc -Destination $PythonRuntimeDst -Recurse
Write-Host "Python runtime bundled" -ForegroundColor Green

# Copy engine folder
$EngineSrc = Join-Path $ProjectRoot "engine"
$EngineDst = Join-Path $ReleaseDir "engine"
if (Test-Path $EngineDst) {
    Remove-Item -Recurse -Force $EngineDst
}
Copy-Item -Path $EngineSrc -Destination $EngineDst -Recurse
Write-Host "Engine bundled" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
