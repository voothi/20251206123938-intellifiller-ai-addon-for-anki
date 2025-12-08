@echo off
setlocal

:: ============================================================================
::  IntelliFiller Release Packager
:: ============================================================================

:: Configuration
:: ----------------------------------------------------------------------------
set "OUTPUT_DIR=C:\Users\voothi\Documents\20251206191819-intellifilter-publication\"

:: Execution
:: ----------------------------------------------------------------------------
echo.
echo [INFO] Saving release to: "%OUTPUT_DIR%"
echo.

if not exist "%OUTPUT_DIR%" (
    echo [INFO] Directory not found. Creating...
    mkdir "%OUTPUT_DIR%"
)

:: Run the python script located in the same directory as this batch file
python.exe "%~dp0package_addon.py" --out "%OUTPUT_DIR%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Packaging failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Done.
pause
