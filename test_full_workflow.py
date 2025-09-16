#!/usr/bin/env python3
"""
Полный тест workflow системы shorts_news
Запускает все компоненты и показывает результат
"""

import sys
import os
import time
import asyncio
sys.path.append('scripts')

def test_full_workflow():
    """Тестирование полного workflow"""
    print("🚀 ТЕСТИРОВАНИЕ ПОЛНОГО WORKFLOW")
    print("=" * 60)

    try:
        # 1. Создаем тестовую новость
        print("1️⃣ Создание тестовой новости...")
        from telegram_bot import NewsTelegramBot

        bot = NewsTelegramBot('config/config.yaml')
        timestamp = str(int(time.time()))

        test_news = {
            'url': f'https://www.cnn.com/politics/test-{timestamp}',
            'title': 'Тест: Байден встречается с европейскими лидерами',
            'description': 'Президент США Джо Байден провел встречу с лидерами Европейского Союза для обсуждения экономического сотрудничества.',
            'source': 'CNN',
            'content_type': 'news'
        }

        news_id = bot._save_parsed_news(test_news, 123456789, 987654321)
        print(f"✅ Тестовая новость создана (ID: {news_id})")

        # 2. Запускаем обработку
        print("\n2️⃣ Запуск обработки новости...")
        from main_orchestrator import ShortsNewsOrchestrator

        orchestrator = ShortsNewsOrchestrator('config/config.yaml')
        orchestrator.initialize_components()

        print("🎬 Начинаем обработку...")
        orchestrator.run_single_cycle()

        print("\n✅ ПОЛНЫЙ WORKFLOW ПРОЙДЕН УСПЕШНО!")
        print("📊 Проверьте канал @tubepush_bot для результатов")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

def test_telegram_only():
    """Только тестирование Telegram публикации"""
    print("📢 ТЕСТИРОВАНИЕ TELEGRAM PUBLISHER")
    print("=" * 40)

    try:
        from telegram_publisher import TelegramPublisher
        import asyncio

        async def test():
            publisher = TelegramPublisher('config/config.yaml')

            if not publisher.is_available():
                print("❌ Publisher недоступен")
                return

            message = "🎯 Тест Shorts News Workflow - сообщение отправлено!"
            success = await publisher.publish_status_update(message)

            if success:
                print("✅ Сообщение отправлено в @tubepush_bot")
            else:
                print("❌ Ошибка отправки сообщения")

        asyncio.run(test())

    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("Выберите тест:")
    print("1 - Полный workflow (создание новости + обработка)")
    print("2 - Только Telegram публикация")
    print("3 - Оба теста")

    choice = input("Ваш выбор (1-3): ").strip()

    if choice in ['1', '3']:
        test_full_workflow()
        if choice == '3':
            print("\n" + "="*60)

    if choice in ['2', '3']:
        test_telegram_only()

    print("\n" + "="*60)
    print("🎉 Тестирование завершено!")
