@echo off
title Islamic Lecture Formatter
cd /d "%~dp0"

:: Auto-detect Python
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set PYTHON=%%i
    goto :found
)

:: Fallback: try common install locations
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    goto :found
)
if exist "%APPDATA%\Local\Programs\Python\Python312\python.exe" (
    set PYTHON=%APPDATA%\Local\Programs\Python\Python312\python.exe
    goto :found
)
if exist "%PYTHONHOME%\python.exe" (
    set PYTHON=%PYTHONHOME%\python.exe
    goto :found
)

echo ERROR: Python not found. Please install Python 3.8+ from python.org
pause
exit /b

:found
echo Using Python: %PYTHON%

:: Check dependencies
echo Checking dependencies...
"%PYTHON%" -m pip install --quiet gradio python-docx pywin32 requests 2>nul
if errorlevel 1 (
    echo NOTE: If you see permission errors above, run this as Administrator:
    echo "%PYTHON%" -m pip install gradio python-docx pywin32 requests
)

echo Starting the Formatter UI...
"%PYTHON%" gradio_app.py
pause
