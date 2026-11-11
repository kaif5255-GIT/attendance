@echo off
title Reset Demo Database
echo ====================================================
echo Resetting database for clean live demonstration...
echo ====================================================

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

%PYTHON_CMD% reset_demo.py
pause
