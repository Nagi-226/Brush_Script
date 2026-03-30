param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "[Brush Script] Building Windows EXE (PyInstaller)..."

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

python --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Python not found. Please install Python 3.11+ and add to PATH."
}

python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

$specPath = "BrushScriptApp.spec"

if (Test-Path $specPath) {
    python -m PyInstaller --noconfirm --clean $specPath
} else {
    $addData = "config.json;."
    python -m PyInstaller --noconfirm --clean --name BrushScriptApp --add-data $addData --collect-all streamlit --collect-all rich --collect-all dotenv --collect-all requests launcher.py
}

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host "[Brush Script] Build finished."
Write-Host "Executable folder: dist/BrushScriptApp/"
Write-Host "Run: dist/BrushScriptApp/BrushScriptApp.exe"
