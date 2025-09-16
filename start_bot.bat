@echo off
echo 🤖 Запуск Telegram бота...
cd /d %~dp0
venv\Scripts\python.exe simple_bot.py
pause
