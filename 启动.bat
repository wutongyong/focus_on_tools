@echo off
chcp 65001 >nul
title Nijika - Midnight Drum Room

echo.
echo  Starting Nijika...
echo.

cd /d "%~dp0"

where npx >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/2] Starting HTTP server (http://localhost:8080)...
start "Nijika-Server" cmd /k "npx -y http-server . -p 8080 --cors"

timeout /t 2 /nobreak >nul

echo [2/2] Opening browser...
start http://localhost:8080

echo.
echo  Done! Close this window to exit (server keeps running).
pause >nul
