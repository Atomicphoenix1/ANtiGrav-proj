@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
title Transcriper Suite
cls

echo ==========================================
echo       Transcriper Suite
echo ==========================================
echo.
echo [1] Prepare Audio (Gradio UI)
echo [2] Format Transcription (Clipboard Monitor)
echo [3] Exit
echo.
set /p choice="Select an option: "

if "%choice%"=="1" (
    echo Launching Audio Preprocessor...
    "C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe" "prepare_audio.py"
) else if "%choice%"=="2" (
    echo Launching Clipboard Monitor...
    "C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe" "ai_studio_formatter.py"
) else (
    exit
)
pause
