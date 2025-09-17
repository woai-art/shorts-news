#!/usr/bin/env python3
"""
Тест интерактивного мониторинга с командой /startat
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = Path('.') / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Добавляем путь к скриптам
sys.path.append(os.path.abspath('scripts'))

def test_interactive_flow():
    """Тестируем интерактивный поток: новость с видео -> команда /startat -> обработка"""
    
    print("🧪 Тест интерактивного мониторинга")
    print("=" * 50)
    
    # Проверяем настройки
    monitor_channel_id = os.getenv("MONITOR_CHANNEL_ID")
    publish_channel_id = os.getenv("PUBLISH_CHANNEL_ID")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    publish_bot_token = os.getenv("PUBLISH_BOT_TOKEN")
    
    print(f"📡 Monitor Channel ID: {monitor_channel_id}")
    print(f"📢 Publish Channel ID: {publish_channel_id}")
    print(f"🤖 Bot Token: {bot_token[:10]}..." if bot_token else "❌ Не установлен")
    print(f"📤 Publish Bot Token: {publish_bot_token[:10]}..." if publish_bot_token else "❌ Не установлен")
    
    if not all([monitor_channel_id, publish_channel_id, bot_token, publish_bot_token]):
        print("❌ Не все переменные окружения настроены!")
        return False
    
    print("\n✅ Все настройки корректны")
    print("\n📋 Инструкция для тестирования:")
    print("1. Запустите монитор: python channel_monitor.py")
    print("2. Отправьте в канал новость с видео (например, AP News)")
    print("3. Монитор должен отправить запрос в группу")
    print("4. Отправьте в группу: /startat <news_id> <seconds>")
    print("5. Монитор должен обработать новость с указанным смещением")
    
    return True

if __name__ == "__main__":
    test_interactive_flow()
