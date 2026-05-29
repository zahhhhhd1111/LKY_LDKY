@echo off
chcp 65001 >nul
cd /d "c:\4code\3lot"

echo ========== Reading ZYY字段名与属性.xlsx ==========
echo.

REM Try Python first (uses built-in zipfile + xml, no extra packages needed)
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [Using Python]
    python read_xlsx.py
    if %ERRORLEVEL% EQU 0 goto :end
    echo Python script had an error, trying alternatives...
    echo.
)

REM Try venv Python
if exist "c:\4code\.venv\Scripts\python.exe" (
    echo [Using venv Python]
    "c:\4code\.venv\Scripts\python.exe" read_xlsx.py
    if %ERRORLEVEL% EQU 0 goto :end
    echo.
)

REM Try Node.js
where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [Using Node.js - checking dependencies]
    if not exist "node_modules\xlsx" (
        echo Installing xlsx package...
        call npm init -y >nul 2>&1
        call npm install xlsx >nul 2>&1
    )
    node read_xlsx.js
    if %ERRORLEVEL% EQU 0 goto :end
    echo.
)

REM Try VBScript (requires Excel installed)
echo [Trying VBScript with Excel COM]
cscript //Nologo read_xlsx.vbs
if %ERRORLEVEL% EQU 0 goto :end

echo.
echo ========== FAILED: No method could read the Excel file ==========
echo Make sure Python or Node.js is installed.
pause
exit /b 1

:end
echo.
echo ========== Done ==========
pause
