@echo off
title Z_PDF_Unlocker PyInstaller Builder

echo ===================================================
echo             Z_PDF_Unlocker Builder
echo ===================================================
echo.

echo Installing PyInstaller packaging tool...
python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo [Warning] Failed to install PyInstaller. Please check internet connection.
    pause
    exit /b %errorlevel%
)

echo.
echo Packaging application (this may take a minute or two)...
pyinstaller --onefile --name=Z_PDF_Unlocker --icon="E:\newbee\Desktop\pdfprint\pdf_filetype_icon_227891.ico" --add-data "templates;templates" --add-data "static;static" app.py

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo [OK] Package compile successful!
    echo The executable is generated at: dist\Z_PDF_Unlocker.exe
    echo ===================================================
) else (
    echo.
    echo [Error] Compile failed. Please check compiler errors above.
)
echo.
pause
