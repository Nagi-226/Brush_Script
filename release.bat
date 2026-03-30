@echo off
setlocal

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "release.ps1" -Clean
if errorlevel 1 (
  echo [ERROR] Release packaging failed.
  pause
  exit /b 1
)

echo [Brush Script] Release ready in .\release
pause

endlocal
