@echo off
title Z_PDF_Unlocker Launcher

echo ===================================================
echo               Z_PDF_Unlocker Local Server
echo ===================================================
echo.

echo Checking and installing Python dependencies...
python -m pip install --user Flask pypdf cryptography
if %errorlevel% neq 0 (
    echo [Info] User-level installation failed. Trying regular installation...
    python -m pip install Flask pypdf cryptography
)

python -c "import flask, pypdf, cryptography" >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Failed to load required Python libraries.
    echo Please run manually: pip install Flask pypdf cryptography
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies check complete!
echo Starting local service...
echo.

python app.py

pause
