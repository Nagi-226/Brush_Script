param(
    [switch]$Clean,
    [string]$Output = "release"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "[Brush Script] Preparing release package..."

if ($Clean) {
    if (Test-Path $Output) { Remove-Item -Recurse -Force $Output }
}

if (-not (Test-Path "dist\BrushScriptApp\BrushScriptApp.exe")) {
    Write-Host "[INFO] EXE not found, running build..."
    powershell -ExecutionPolicy Bypass -File "build_exe.ps1"
}

if (-not (Test-Path "dist\BrushScriptApp\BrushScriptApp.exe")) {
    throw "Build output missing. dist/BrushScriptApp/BrushScriptApp.exe not found."
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null

Copy-Item -Recurse -Force "dist\BrushScriptApp\*" $Output

$docs = @(
    "README.md",
    "PROJECT_OVERVIEW.md",
    ".env.example"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Copy-Item -Force $doc $Output
    }
}

Write-Host "[Brush Script] Release package ready at: $Output"
Write-Host "Run: $Output\BrushScriptApp.exe"
