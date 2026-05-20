@echo off
cd /d "%~dp0"
if exist livekit-server.exe (
    echo Starting LiveKit server on ws://localhost:7880 (devkey/secret)...
    echo Leave this window open while testing the voice agent.
    livekit-server.exe --dev
) else (
    echo livekit-server.exe not found. Run setup from repo root once.
    exit /b 1
)
