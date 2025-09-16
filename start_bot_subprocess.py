#!/usr/bin/env python3
"""
Запуск Telegram бота в отдельном subprocess
"""

import subprocess
import sys
import os

def main():
    """Запуск бота в subprocess"""
    print("🤖 Запуск Telegram бота в отдельном процессе...")

    # Путь к Python в виртуальном окружении
    python_exe = os.path.join("venv", "Scripts", "python.exe")

    # Команда для запуска
    cmd = [python_exe, "-c", """
import sys
sys.path.append('scripts')
from telegram_bot import NewsTelegramBot
import asyncio

async def run():
    bot = NewsTelegramBot('config/config.yaml')
    await bot.run_bot()

asyncio.run(run())
"""]

    try:
        # Запускаем в отдельном процессе
        process = subprocess.Popen(cmd, cwd=os.getcwd())
        print(f"✅ Бот запущен в процессе PID: {process.pid}")
        print("Для остановки нажмите Ctrl+C")

        # Ждем завершения
        process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        if 'process' in locals():
            process.terminate()
        print("✅ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
