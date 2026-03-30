@echo off
setlocal

cd /d "%~dp0"

if not exist "dist\BrushScriptApp\BrushScriptApp.exe" (
  echo [INFO] EXE not found. Building now...
  powershell -ExecutionPolicy Bypass -File "build_exe.ps1"
  if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
  )
)

echo [Brush Script] Launching packaged app...
start "" "dist\BrushScriptApp\BrushScriptApp.exe"

endlocal
