@echo off
title OmegaAI Service Installer
echo ============================================================
echo           INSTALLING OMEGA AI BACKGROUND DAEMON
echo ============================================================
echo.

:: Check if OmegaAI.exe exists in the current folder
if not exist "OmegaAI.exe" (
    echo [ERROR] OmegaAI.exe not found in this folder!
    echo Please ensure OmegaAI.exe is placed next to this installer.
    echo.
    pause
    exit /b 1
)

:: Launch the executable to trigger its self-installer popup
echo [*] Launching OmegaAI Installer...
start "" "OmegaAI.exe"

echo.
echo [SUCCESS] Installer launched! Please follow the popup instructions.
echo.
pause
