@echo off
title OmegaAI Service Uninstaller
echo ============================================================
echo          UNINSTALLING OMEGA AI BACKGROUND DAEMON
echo ============================================================
echo.

echo [*] Terminating running OmegaAI processes...
taskkill /IM OmegaAI.exe /F >nul 2>&1

echo [*] Removing startup registry entries...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OmegaAI" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaAI" /f >nul 2>&1

echo.
echo [SUCCESS] OmegaAI background service successfully removed.
echo.
pause
