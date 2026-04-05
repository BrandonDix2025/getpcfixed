@echo off
title GetPCFixed Build Script
echo.
echo  ==========================================
echo   GetPCFixed Build Script
echo  ==========================================
echo.

echo  [1/2] Building executable with PyInstaller...
pyinstaller GetPCFixed.spec --clean
if %ERRORLEVEL% neq 0 (
    echo  ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo  Done.
echo.

echo  [2/2] Compiling installer with Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Users\%USERNAME%\AppData\Local\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo  ERROR: Inno Setup 6 not found in standard locations.
    echo  Run this to find it: dir /s /b "C:\" ISCC.exe 2>nul
    pause
    exit /b 1
)
%ISCC% installer.iss
echo.
echo  BUILD COMPLETE
echo  Installer: installer_output\GetPCFixed_Setup_v0.5.exe
echo.
pause