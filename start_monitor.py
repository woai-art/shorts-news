#!/usr/bin/env python3
"""
Запуск монитора канала в фоне
"""

import subprocess
import sys
import os
import time

def main():
    """Запуск монитора канала"""
    print("🚀 Запуск монитора Telegram канала...")

    # Путь к Python
    python_exe = sys.executable

    # Команда для запуска монитора
    cmd = [python_exe, "channel_monitor.py"]

    try:
        print("📡 Мониторинг канала -1003056499503 запущен")
        print("📢 Публикация результатов в -1002685642224")
        print("Для остановки нажмите Ctrl+C")
        print("-" * 50)

        # Запускаем монитор
        process = subprocess.Popen(cmd)

        # Ждем завершения
        process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Остановка монитора...")
        if 'process' in locals():
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
        print("✅ Монитор остановлен")

if __name__ == "__main__":
    main()
