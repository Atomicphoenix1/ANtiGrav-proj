@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
title AI Studio Formatter
echo Starting AI Studio Formatter...
"C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe" "ai_studio_formatter.py"
pause
