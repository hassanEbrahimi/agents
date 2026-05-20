@echo off
cd /d "%~dp0"
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

set LK_EXE=%~dp0tools\livekit-server.exe
set LK_PORT=7880

:: Start local LiveKit if port is free
powershell -NoProfile -Command ^
  "$p=%LK_PORT%; $inUse = (Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded; exit ([int]$inUse)" >nul 2>&1
if errorlevel 1 (
    echo LiveKit already running on port %LK_PORT%.
) else (
    if not exist "%LK_EXE%" (
        echo ERROR: %LK_EXE% not found.
        exit /b 1
    )
    echo Starting LiveKit server in a new window...
    start "LiveKit Server" "%LK_EXE%" --dev
    echo Waiting for LiveKit to start...
    timeout /t 3 /nobreak >nul
)

echo.
echo Starting voice agent. Speak into your microphone. Press Ctrl+C to stop.
echo.
py myagent.py console
endlocal
