--- build_windows.bat (原始)


+++ build_windows.bat (修改后)
@echo off
echo ========================================
echo Building KeyboardMapperPro for Windows
echo ========================================
echo.

REM Install pyinstaller if not already installed
pip install pyinstaller --quiet

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build the executable
echo Building executable...
pyinstaller --onefile --windowed --name KeyboardMapperPro --icon=NONE keyboard_mapper_pro.py

if exist "dist\KeyboardMapperPro.exe" (
    echo.
    echo ========================================
    echo SUCCESS! Executable created:
    echo dist\KeyboardMapperPro.exe
    echo ========================================
    echo.
    echo File size:
    dir dist\KeyboardMapperPro.exe | find "KeyboardMapperPro.exe"
    echo.
    echo You can now distribute this single .exe file!
) else (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)

pause