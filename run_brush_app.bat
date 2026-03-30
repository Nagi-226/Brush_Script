@echo off
setlocal

cd /d "%~dp0"

echo [Brush Script] Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Please install Python 3.11+ and add it to PATH.
  pause
  exit /b 1
)

echo [Brush Script] Checking Streamlit...
python -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo [Brush Script] Installing dependencies from requirements.txt...
  pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
  )
)

echo [Brush Script] Launching web app...
start "" http://localhost:8501
streamlit run app.py --server.headless true --browser.gatherUsageStats false

if errorlevel 1 (
  echo [ERROR] App exited unexpectedly.
  pause
  exit /b 1
)

endlocal
