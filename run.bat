@echo off
title Employee Attendance System Server
echo ========================================================
echo   Starting Employee Attendance Management System...
echo ========================================================

cd /d "%~dp0"

set "PYTHON_CMD="

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if "%PYTHON_CMD%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    set PYTHON_CMD=python
)

echo Python Path: %PYTHON_CMD%
echo.
echo --------------------------------------------------------
echo 1. Opening web browser at: http://127.0.0.1:8000
echo 2. Default Admin Credentials:
echo    Email:    admin@gmail.com
echo    Password: Admin@12345
echo --------------------------------------------------------
echo.
echo Server is running. KEEP THIS WINDOW OPEN while using the app!
echo Press Ctrl + C to stop the server anytime.
echo.

start "" "http://127.0.0.1:8000"

%PYTHON_CMD% -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

pause
