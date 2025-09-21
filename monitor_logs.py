#!/usr/bin/env python3
"""
Мониторинг логов системы
"""

import time
import os
from pathlib import Path

def monitor_logs():
    """Мониторит логи системы в реальном времени"""
    log_file = Path("logs/shorts_news.log")
    
    if not log_file.exists():
        print("❌ Лог файл не найден. Создаем...")
        log_file.parent.mkdir(exist_ok=True)
        log_file.touch()
    
    print("🔍 Мониторинг логов системы...")
    print("📋 Отправьте ссылку на Politico в канал @tubepull_bot")
    print("⏹️  Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # Переходим в конец файла
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(line.strip())
                else:
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\n✅ Мониторинг остановлен")

if __name__ == "__main__":
    monitor_logs()
