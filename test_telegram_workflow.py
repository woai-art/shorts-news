#!/usr/bin/env python3
"""
Тест нового Telegram workflow системы shorts_news
"""

import os
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_parser():
    """Тест веб-парсера"""
    logger.info("🧪 Тест Web Parser...")

    try:
        from scripts.web_parser import WebParser

        parser = WebParser('config/config.yaml')

        # Тестовые URL
        test_urls = [
            "https://www.bbc.com/news/world-us-canada-67443258",
            "https://www.cnn.com/politics/",
        ]

        for url in test_urls:
            logger.info(f"Парсинг: {url}")
            result = parser.parse_url(url)

            if result.get('success'):
                logger.info(f"✅ Успешно: {result.get('title', 'Без заголовка')[:50]}...")
                logger.info(f"   Источник: {result.get('source', 'Неизвестен')}")
                logger.info(f"   Изображений: {len(result.get('images', []))}")
            else:
                logger.warning(f"⚠️ Не удалось: {result.get('error', 'Неизвестная ошибка')}")

        parser.close()
        logger.info("✅ Web Parser тест завершен")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка в Web Parser: {e}")
        return False

def test_telegram_bot_db():
    """Тест базы данных Telegram бота"""
    logger.info("🧪 Тест Telegram Bot Database...")

    try:
        from scripts.telegram_bot import NewsTelegramBot
        import time

        bot = NewsTelegramBot('config/config.yaml')

        # Тест получения новостей
        pending_news = bot.get_pending_news(limit=5)
        logger.info(f"Найдено необработанных новостей: {len(pending_news)}")

        # Тест сохранения новости с уникальным URL
        timestamp = int(time.time())
        test_data = {
            'url': f'https://example.com/test-news-{timestamp}',
            'title': 'Тестовая новость для проверки',
            'description': 'Тестовое описание новости',
            'source': 'Test Source',
            'content_type': 'test'
        }

        news_id = bot._save_parsed_news(test_data, 123456789, 987654321)
        logger.info(f"Создана тестовая новость с ID: {news_id}")

        # Тест отметки как обработанной
        bot.mark_news_processed(news_id)
        logger.info("Новость отмечена как обработанная")

        logger.info("✅ Telegram Bot Database тест завершен")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка в Telegram Bot Database: {e}")
        return False

def test_llm_with_grounding():
    """Тест LLM с Google Search Grounding"""
    logger.info("🧪 Тест LLM с Grounding...")

    try:
        from scripts.llm_processor import LLMProcessor

        processor = LLMProcessor('config/config.yaml')

        # Тестовая новость для проверки фактов
        test_news = {
            'id': 999,
            'title': 'Президент Байден встретился с лидерами G7',
            'description': 'Джо Байден обсудил экономические вопросы с лидерами стран G7 на саммите в Германии.',
            'source': 'Reuters',
            'published': '2024-06-15T10:00:00Z',
            'category': 'Политика'
        }

        logger.info("Обработка новости с проверкой фактов...")
        result = processor.process_news_for_shorts(test_news)

        if result.get('status') == 'success':
            logger.info("✅ LLM обработка успешна")
            logger.info(f"   Short text: {result.get('short_text', '')[:50]}...")
            logger.info(f"   Fact check score: {result.get('fact_verification', {}).get('accuracy_score', 'N/A')}")
        else:
            logger.warning(f"⚠️ Ошибка LLM обработки: {result.get('error', 'Неизвестная ошибка')}")

        logger.info("✅ LLM Grounding тест завершен")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка в LLM Grounding: {e}")
        return False

def test_orchestrator():
    """Тест главного оркестратора"""
    logger.info("🧪 Тест Orchestrator...")

    try:
        from scripts.main_orchestrator import ShortsNewsOrchestrator

        orchestrator = ShortsNewsOrchestrator('config/config.yaml')
        orchestrator.initialize_components()

        logger.info("✅ Orchestrator инициализация успешна")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка в Orchestrator: {e}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    logger.info("🚀 Запуск комплексного тестирования Telegram Workflow")
    logger.info("=" * 60)

    tests = [
        ("Web Parser", test_web_parser),
        ("Telegram Bot DB", test_telegram_bot_db),
        ("LLM Grounding", test_llm_with_grounding),
        ("Orchestrator", test_orchestrator),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*40}")
        logger.info(f"Запуск теста: {test_name}")
        logger.info('='*40)

        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))

    # Вывод результатов
    logger.info("\n" + "=" * 60)
    logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    logger.info("=" * 60)

    successful_tests = 0
    total_tests = len(results)

    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        logger.info(f"{status}: {test_name}")

    successful_tests = sum(1 for _, success in results if success)

    logger.info("-" * 60)
    logger.info(f"ИТОГО: {successful_tests}/{total_tests} тестов пройдено")

    if successful_tests == total_tests:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        logger.info("✅ Telegram Workflow готов к работе")
        return True
    else:
        logger.warning("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        logger.info("🔧 Проверьте конфигурацию и API ключи")
        return False

def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description='Test Telegram Workflow')
    parser.add_argument('--web-parser', action='store_true',
                       help='Тест только Web Parser')
    parser.add_argument('--telegram-db', action='store_true',
                       help='Тест только Telegram DB')
    parser.add_argument('--llm-grounding', action='store_true',
                       help='Тест только LLM Grounding')
    parser.add_argument('--orchestrator', action='store_true',
                       help='Тест только Orchestrator')
    parser.add_argument('--all', action='store_true',
                       help='Запуск всех тестов')

    args = parser.parse_args()

    # Если нет аргументов, запустить все тесты
    if not any([args.web_parser, args.telegram_db, args.llm_grounding, args.orchestrator, args.all]):
        args.all = True

    try:
        if args.all:
            success = run_all_tests()
        else:
            success = True
            if args.web_parser:
                success &= test_web_parser()
            if args.telegram_db:
                success &= test_telegram_bot_db()
            if args.llm_grounding:
                success &= test_llm_with_grounding()
            if args.orchestrator:
                success &= test_orchestrator()

        if success:
            logger.info("\n🎉 Тестирование завершено успешно!")
            sys.exit(0)
        else:
            logger.error("\n❌ Обнаружены ошибки в тестировании")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n👋 Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
