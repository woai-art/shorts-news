@echo off
chcp 65001 > nul

echo ========================================
echo.
echo    TELEGRAM CHANNEL MONITOR
echo.
echo ========================================
echo.
echo Activating virtual environment...
call .\\venv\\Scripts\\activate.bat

echo.
echo Starting channel_monitor.py...
echo Press Ctrl+C to stop the monitor.
echo.

python channel_monitor.py

echo.
echo Monitor stopped.
pause
