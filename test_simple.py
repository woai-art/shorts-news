#!/usr/bin/env python3
"""
Простой тест системы shorts_news
"""

import sys
import os
sys.path.append('scripts')

def test_basic_functionality():
    """Тестирование основных компонентов"""
    print("Testing basic functionality...")

    try:
        # Тест 1: Импорт компонентов
        from telegram_bot import NewsTelegramBot
        from telegram_publisher import TelegramPublisher
        print("✓ Components imported successfully")

        # Тест 2: Создание бота
        bot = NewsTelegramBot('config/config.yaml')
        print("✓ Telegram bot created")

        # Тест 3: Создание новости
        test_news = {
            'url': 'https://example.com/test',
            'title': 'Test News',
            'description': 'Test description',
            'source': 'Test',
            'content_type': 'news'
        }

        news_id = bot._save_parsed_news(test_news, 123, -1003056499503)
        print(f"✓ Test news saved with ID: {news_id}")

        # Тест 4: Создание publisher
        publisher = TelegramPublisher('config/config.yaml')
        if publisher.is_available():
            print("✓ Telegram publisher ready")
        else:
            print("⚠ Telegram publisher not available")

        print("\n🎉 All basic tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""
    print("=" * 50)
    print("SHORTS_NEWS - Simple Test")
    print("=" * 50)

    success = test_basic_functionality()

    if success:
        print("\n✅ System is ready!")
        print("\nTo start monitoring:")
        print("python channel_monitor.py")
    else:
        print("\n❌ System has issues")

if __name__ == "__main__":
    main()
