@echo off
title Omega Guard Sentinel Client Agent Launcher
echo =======================================================
echo     STARTING OMEGA SENTINEL CLIENT AGENT IN USER SESSION
echo =======================================================
echo.
cd /d "%~dp0backend"
echo [1/2] Activating secure Python environment...
:: call .\venv\Scripts\activate.bat
echo [2/2] Launching client agent on port 8000...
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Server stopped. Press any key to exit.
pause
