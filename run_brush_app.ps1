$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

Write-Host "[Brush Script] Checking Python..."
try {
    $null = python --version
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.11+ and add it to PATH."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[Brush Script] Checking Streamlit..."
try {
    python -c "import streamlit" | Out-Null
} catch {
    Write-Host "[Brush Script] Installing dependencies from requirements.txt..."
    try {
        pip install -r requirements.txt
    } catch {
        Write-Host "[ERROR] Failed to install dependencies."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[Brush Script] Launching web app..."
Start-Process "http://localhost:8501"
streamlit run app.py --server.headless true --browser.gatherUsageStats false

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] App exited unexpectedly."
    Read-Host "Press Enter to exit"
    exit 1
}
